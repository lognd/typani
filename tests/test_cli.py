"""Tests for the `typani` console script: parser, config layering, App dispatch (T-0037)."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from typani import Err, Ok
from typani.__main__ import build_parser, main
from typani.app import App, AppConfig, ConfigError
from typani.app.config import bootstrap_log_level
from typani.lint.options import LintOptions
from typani.logging import configure, get_logger
from typani.logging.filter import BelowLevelFilter
from typani.logging.formatter import TypaniFormatter
from typani.logging.levels import LEVEL_NAMES, resolve_level

_ROOT = Path(__file__).resolve().parents[1]

_CLEAN = """
def f(r):
    if r.is_ok:
        return r.unwrap()
    return None
"""

_DIRTY = """
def f(r):
    if r.is_ok():
        return None
    return None
"""


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    """Keep the layering tests off the developer's real env and pyproject.toml."""
    for name in (
        "TYPANI_LOG_LEVEL",
        "TYPANI_LINT_PATHS",
        "TYPANI_LINT_EXCLUDE",
        "TYPANI_LINT_SELECT",
        "TYPANI_LINT_IGNORE",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


def _tree(tmp_path: Path, source: str) -> Path:
    """Write `source` into a fresh directory and return that directory."""
    target = tmp_path / "tree"
    target.mkdir(exist_ok=True)
    (target / "mod.py").write_text(textwrap.dedent(source))
    return target


def _parse(argv: list[str]) -> argparse.Namespace:
    """Parse argv with the real top-level parser."""
    return build_parser().parse_args(argv)


# --- end-to-end CLI ---------------------------------------------------------


# frob:tests src/typani/__main__.py::main
def test_lint_subcommand_clean_tree(tmp_path: Path) -> None:
    assert main(["lint", str(_tree(tmp_path, _CLEAN))]) == 0


# frob:tests src/typani/__main__.py::main
def test_lint_subcommand_reports_errors(tmp_path: Path, capsys) -> None:
    assert main(["lint", str(_tree(tmp_path, _DIRTY))]) == 1
    assert "TYP001" in capsys.readouterr().out


# frob:tests src/typani/__main__.py::main
def test_lint_subcommand_forwards_flags(tmp_path: Path, capsys) -> None:
    """`--json` is defined once, by typani.lint, and must survive the dispatch."""
    assert main(["lint", "--json", str(_tree(tmp_path, _DIRTY))]) == 1
    assert capsys.readouterr().out.lstrip().startswith("{")


# frob:tests src/typani/__main__.py::main
def test_no_subcommand_is_a_config_error(capsys) -> None:
    assert main([]) == 2
    assert "usage: typani" in capsys.readouterr().err


# frob:tests src/typani/__main__.py::main
def test_unknown_subcommand_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["nope"])
    assert excinfo.value.code == 2


# frob:tests src/typani/__main__.py::main
def test_bad_log_level_is_a_config_error() -> None:
    assert main(["--log-level", "bogus", "lint", "."]) == 2


# frob:tests src/typani/__main__.py::build_parser
def test_version_flag_exits_zero(capsys) -> None:
    from typani._version import __version__

    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


# frob:tests src/typani/__main__.py::build_parser
def test_log_level_accepted_on_either_side_of_the_subcommand() -> None:
    """A subparser default must not erase the top-level parser's value."""
    assert _parse(["--log-level", "debug", "lint"]).log_level == "debug"
    assert _parse(["lint", "--log-level", "debug"]).log_level == "debug"
    assert bootstrap_log_level(_parse(["lint"])) is None


# --- AppConfig layering -----------------------------------------------------


# frob:tests src/typani/app/config.py::AppConfig.from_external
def test_from_external_defaults_when_nothing_is_set() -> None:
    result = AppConfig.from_external(_parse(["lint"]))
    assert isinstance(result, Ok)
    cfg = result.danger_ok
    assert cfg.command == "lint"
    assert cfg.log_level == "WARNING"
    assert cfg.lint == LintOptions()


# frob:tests src/typani/app/config.py::AppConfig.from_external
def test_from_external_reports_a_missing_subcommand() -> None:
    result = AppConfig.from_external(_parse([]))
    assert isinstance(result, Err)
    assert result.danger_err is ConfigError.NoCommand


# frob:tests src/typani/app/config.py::AppConfig.from_external
@pytest.mark.skipif(sys.version_info < (3, 11), reason="no tomllib before 3.11")
def test_cli_overrides_env_overrides_file(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "pyproject.toml"
    config.write_text(
        '[tool.typani]\nlog_level = "error"\n'
        '[tool.typani.lint]\npaths = ["from_file"]\nselect = ["TYP001"]\n'
        "no_info = true\n"
    )
    monkeypatch.setenv("TYPANI_LINT_SELECT", "TYP002,TYP003")

    result = AppConfig.from_external(_parse(["lint", "from_cli"]), config)
    assert isinstance(result, Ok)
    cfg = result.danger_ok
    assert cfg.lint.paths == ("from_cli",)  # CLI beats env and file
    assert cfg.lint.select == ("TYP002", "TYP003")  # env beats file
    assert cfg.lint.no_info is True  # file beats the default
    assert cfg.log_level == "ERROR"


# frob:tests src/typani/app/config.py::AppConfig.from_external
def test_cli_overrides_env(tmp_path: Path, monkeypatch) -> None:
    """The two layers that need no TOML reader, so this holds on 3.10 too."""
    monkeypatch.setenv("TYPANI_LINT_PATHS", "from_env")
    monkeypatch.setenv("TYPANI_LINT_IGNORE", "TYP004")

    from_env = AppConfig.from_external(_parse(["lint"]), tmp_path / "absent.toml")
    assert isinstance(from_env, Ok)
    assert from_env.danger_ok.lint.paths == ("from_env",)
    assert from_env.danger_ok.lint.ignore == ("TYP004",)

    from_cli = AppConfig.from_external(
        _parse(["lint", "from_cli"]), tmp_path / "absent.toml"
    )
    assert isinstance(from_cli, Ok)
    assert from_cli.danger_ok.lint.paths == ("from_cli",)


# frob:tests src/typani/app/config.py::AppConfig.from_external
def test_missing_config_file_is_not_an_error(tmp_path: Path) -> None:
    result = AppConfig.from_external(_parse(["lint"]), tmp_path / "absent.toml")
    assert isinstance(result, Ok)


# frob:tests src/typani/app/config.py::AppConfig.from_external
@pytest.mark.skipif(sys.version_info < (3, 11), reason="no tomllib before 3.11")
def test_unparseable_config_file_is_a_config_error(tmp_path: Path) -> None:
    config = tmp_path / "pyproject.toml"
    config.write_text("this is not = = toml\n")
    result = AppConfig.from_external(_parse(["lint"]), config)
    assert isinstance(result, Err)
    assert result.danger_err is ConfigError.BadConfigFile


# frob:tests src/typani/app/config.py::AppConfig.from_external
@pytest.mark.skipif(sys.version_info < (3, 11), reason="no tomllib before 3.11")
def test_non_table_lint_section_is_a_config_error(tmp_path: Path) -> None:
    config = tmp_path / "pyproject.toml"
    config.write_text('[tool]\ntypani = { lint = "nope" }\n')
    result = AppConfig.from_external(_parse(["lint"]), config)
    assert isinstance(result, Err)
    assert result.danger_err is ConfigError.BadConfigValue


# frob:tests src/typani/app/config.py::bootstrap_log_level
def test_bootstrap_log_level_falls_back_to_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("TYPANI_LOG_LEVEL", "debug")
    assert bootstrap_log_level(_parse(["lint"])) == "debug"
    assert bootstrap_log_level(_parse(["--log-level", "info", "lint"])) == "info"


# --- LintOptions ------------------------------------------------------------


# frob:tests src/typani/lint/options.py::LintOptions.from_mapping
def test_from_mapping_ignores_unknown_and_none_values() -> None:
    options = LintOptions.from_mapping(
        {"paths": None, "select": "TYP001", "unrelated": "x", "no_info": True}
    )
    assert options.paths == (".",)
    assert options.select == ("TYP001",)
    assert options.no_info is True


# --- App --------------------------------------------------------------------


# frob:tests src/typani/app/app.py::App.__call__
def test_app_runs_the_lint_command(tmp_path: Path) -> None:
    cfg = AppConfig(
        command="lint", lint=LintOptions(paths=(str(_tree(tmp_path, _DIRTY)),))
    )
    assert App(cfg)() == 1


# frob:tests src/typani/app/app.py::App.__call__
def test_app_rejects_a_command_it_has_no_runner_for() -> None:
    assert App(AppConfig(command="nonexistent"))() == 2


# --- logging channel --------------------------------------------------------


# frob:tests src/typani/logging/logger.py::configure
def test_configure_is_idempotent_and_root_safe() -> None:
    root_handlers = list(logging.getLogger().handlers)
    configure()
    configure("info")
    typani_logger = logging.getLogger("typani")
    # Count only ours: pytest's caplog attaches handlers of its own here.
    ours = [
        h for h in typani_logger.handlers if isinstance(h.formatter, TypaniFormatter)
    ]
    assert len(ours) == 2
    assert typani_logger.level == logging.INFO
    assert logging.getLogger().handlers == root_handlers


# frob:tests src/typani/logging/logger.py::configure
def test_configure_ignores_an_unknown_level() -> None:
    configure("info")
    configure("bogus")
    assert logging.getLogger("typani").level == logging.INFO


# frob:tests src/typani/logging/levels.py::resolve_level
def test_resolve_level_accepts_the_standard_names() -> None:
    """Case-insensitive, and None -- never a raise -- for anything else."""
    assert resolve_level("debug") == logging.DEBUG
    assert resolve_level("WARNING") == logging.WARNING
    assert resolve_level("Error") == logging.ERROR
    assert resolve_level("bogus") is None
    assert resolve_level("") is None
    # Every accepted name must round-trip to the stdlib's own number.
    for name, number in LEVEL_NAMES.items():
        assert logging.getLevelName(number) == name


# frob:tests src/typani/logging/filter.py::BelowLevelFilter
def test_below_level_filter_rejects_a_bad_bound() -> None:
    """A bound that is not a level name is a programmer bug, not a config value."""
    with pytest.raises(ValueError, match="not a logging level name"):
        BelowLevelFilter("bogus")


# frob:tests src/typani/logging/filter.py::BelowLevelFilter
def test_below_level_filter_splits_at_its_bound() -> None:
    """Diagnostics go to stdout only while they stay below WARNING."""
    below = BelowLevelFilter("WARNING")

    def record(level: int) -> logging.LogRecord:
        return logging.LogRecord("typani", level, __file__, 1, "m", None, None)

    assert below.filter(record(logging.DEBUG)) is True
    assert below.filter(record(logging.INFO)) is True
    assert below.filter(record(logging.WARNING)) is False
    assert below.filter(record(logging.ERROR)) is False


# frob:tests src/typani/logging/formatter.py::TypaniFormatter
def test_formatter_prefixes_only_warnings_and_above() -> None:
    """The level prefix is what separates a diagnostic from ordinary output."""
    plain = TypaniFormatter()

    def record(level: int) -> logging.LogRecord:
        return logging.LogRecord("typani", level, __file__, 1, "m", None, None)

    assert plain.format(record(logging.INFO)) == "m"
    assert plain.format(record(logging.ERROR)) == "ERROR: m"
    assert TypaniFormatter(show_level=True).format(record(logging.INFO)) == "INFO: m"


# frob:tests src/typani/logging/logger.py::get_logger
def test_get_logger_attaches_nothing() -> None:
    """Importing typani as a library must never install handlers of its own."""
    assert get_logger("typani.lint.somewhere").handlers == []


# --- packaging --------------------------------------------------------------


# frob:tests src/typani/lint/__main__.py::main kind="integration"
def test_module_form_still_works(tmp_path: Path) -> None:
    """`python -m typani.lint` must keep behaving exactly as before."""
    proc = subprocess.run(
        [sys.executable, "-m", "typani.lint", str(_tree(tmp_path, _DIRTY))],
        capture_output=True,
        text=True,
        cwd=_ROOT,
    )
    assert proc.returncode == 1
    assert "TYP001" in proc.stdout


# frob:tests src/typani/__main__.py::main kind="integration"
def test_package_module_form_works(tmp_path: Path) -> None:
    """`python -m typani lint` is the console script's module equivalent."""
    proc = subprocess.run(
        [sys.executable, "-m", "typani", "lint", str(_tree(tmp_path, _DIRTY))],
        capture_output=True,
        text=True,
        cwd=_ROOT,
    )
    assert proc.returncode == 1
    assert "TYP001" in proc.stdout


# frob:tests pyproject.toml kind="integration"
def test_console_script_entry_point_is_declared() -> None:
    """The [project.scripts] entry `uv tool install` needs must stay declared."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    data = tomllib.loads((_ROOT / "pyproject.toml").read_text())
    assert data["project"]["scripts"]["typani"] == "typani.__main__:main"
