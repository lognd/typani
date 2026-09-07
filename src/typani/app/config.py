"""Layered `typani` CLI settings: CLI flags > env > pyproject > defaults."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from typani.app.errors import ConfigError
from typani.lint.options import LintOptions, namespace_to_mapping
from typani.logging import get_logger
from typani.logging.levels import resolve_level
from typani.result import Err, Ok, Result

_log = get_logger(__name__)

#: The default minimum level for typani's own diagnostics. A module constant
#: rather than a read of the dataclass field: `slots=True` replaces class
#: attributes with slot descriptors, so `cls.log_level` is not the default.
DEFAULT_LOG_LEVEL = "WARNING"

#: Where the file layer is read from, relative to the invocation directory.
DEFAULT_CONFIG_FILE = Path("pyproject.toml")

#: The table `[tool.typani.lint]` lives under in that file.
_TOOL_TABLE = ("tool", "typani")

#: Environment overrides, mapped to the config key each one sets. Comma-split
#: for the list-valued keys; `TYPANI_PURE` is deliberately absent -- that one
#: belongs to the runtime backend selector in `typani._impl`, not the CLI.
_LOG_LEVEL_ENV = "TYPANI_LOG_LEVEL"

_ENV_KEYS = {
    _LOG_LEVEL_ENV: "log_level",
    "TYPANI_LINT_PATHS": "paths",
    "TYPANI_LINT_EXCLUDE": "exclude",
    "TYPANI_LINT_SELECT": "select",
    "TYPANI_LINT_IGNORE": "ignore",
}

_LIST_KEYS = frozenset({"paths", "exclude", "select", "ignore"})


#: Not a pydantic BaseModel, which is what the sibling CLI repos use: typani
#: ships with an empty runtime dependency list by contract (pydantic is an
#: extra), and `uvx typani lint` must not drag a dependency into a tree that
#: only wanted the checker. A frozen dataclass plus typani's own Result is the
#: dependency-free equivalent -- and dogfoods the library the CLI ships with.
# frob:doc docs/cli.md#appconfig
# frob:tests tests/test_cli.py::test_from_external_defaults_when_nothing_is_set
# frob:ticket T-0037
@dataclass(frozen=True, slots=True)
class AppConfig:
    """One `typani` invocation: which command, how noisy, and that command's options."""

    command: str = "lint"
    log_level: str = DEFAULT_LOG_LEVEL
    lint: LintOptions = field(default_factory=LintOptions)

    # frob:doc docs/cli.md#appconfig
    # frob:tests tests/test_cli.py::test_cli_overrides_env
    # frob:tests tests/test_cli.py::test_cli_overrides_env_overrides_file
    # frob:ticket T-0037
    @classmethod
    def from_external(
        cls,
        args: argparse.Namespace,
        config_file: Path | None = None,
    ) -> Result[AppConfig, ConfigError]:
        """Layer CLI args over env vars over `[tool.typani]` over field defaults.

        Never call `AppConfig(...)` directly from outside: this is the only
        constructor that applies the precedence rules, and the only one that
        reports a bad log level or an unreadable config file as a value.
        """
        command = getattr(args, "command", None)
        if command is None:
            _log.error("from_external: no subcommand given")
            return Err(ConfigError.NoCommand)

        file_result = _read_config_file(
            config_file if config_file is not None else DEFAULT_CONFIG_FILE
        )
        if isinstance(file_result, Err):
            return Err(file_result.danger_err)
        file_cfg = file_result.danger_ok

        env_cfg = _env_overrides()
        cli_cfg = dict(namespace_to_mapping(args))
        if (level := getattr(args, "log_level", None)) is not None:
            cli_cfg["log_level"] = level

        merged: dict[str, Any] = {**file_cfg, **env_cfg, **cli_cfg}
        _log.debug("from_external: file=%s env=%s cli=%s", file_cfg, env_cfg, cli_cfg)

        log_level = str(merged.get("log_level", DEFAULT_LOG_LEVEL)).upper()
        if resolve_level(log_level) is None:
            _log.error("from_external: %r is not a logging level name", log_level)
            return Err(ConfigError.BadLogLevel)

        cfg = cls(
            command=str(command),
            log_level=log_level,
            lint=LintOptions.from_mapping(merged),
        )
        _log.info("from_external: resolved %r", cfg)
        return Ok(cfg)


# frob:doc docs/cli.md#appconfig
# frob:tests tests/test_cli.py::test_bootstrap_log_level_falls_back_to_the_environment
# frob:ticket T-0037
def bootstrap_log_level(args: argparse.Namespace) -> str | None:
    """Return the CLI-or-env log level, before the full layering has run.

    `from_external` emits its own diagnostics, so the channel has to be at
    the right level *before* it is called; only the two layers that are
    readable without touching the filesystem are consulted here.
    """
    level = getattr(args, "log_level", None)
    if level is None:
        level = os.environ.get(_LOG_LEVEL_ENV)
    return level


def _read_config_file(path: Path) -> Result[dict[str, Any], ConfigError]:
    """Read `[tool.typani]` and `[tool.typani.lint]` from a pyproject.toml, if present.

    A missing file is not an error -- the file layer is optional. On 3.10,
    where `tomllib` does not exist and typani has no runtime dependency to
    fall back on, the layer is skipped with a warning rather than failing
    an invocation that would otherwise have worked.
    """
    try:
        import tomllib
    except ModuleNotFoundError:
        _log.info(
            "_read_config_file: tomllib is unavailable before 3.11, "
            "so [tool.typani] in %s is ignored on this interpreter",
            path,
        )
        return Ok({})

    if not path.is_file():
        _log.debug("_read_config_file: no config file at %s", path)
        return Ok({})

    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        _log.error("_read_config_file: %s did not parse as TOML: %s", path, exc)
        return Err(ConfigError.BadConfigFile)
    except OSError as exc:
        _log.error("_read_config_file: could not read %s: %s", path, exc)
        return Err(ConfigError.BadConfigFile)

    table: Any = data
    for key in _TOOL_TABLE:
        table = table.get(key, {}) if isinstance(table, dict) else {}
    if not isinstance(table, dict):
        _log.error("_read_config_file: [tool.typani] in %s is not a table", path)
        return Err(ConfigError.BadConfigValue)

    values: dict[str, Any] = {}
    if isinstance(level := table.get("log_level"), str):
        values["log_level"] = level
    lint_table = table.get("lint", {})
    if isinstance(lint_table, dict):
        values.update(lint_table)
    else:
        _log.error("_read_config_file: [tool.typani.lint] in %s is not a table", path)
        return Err(ConfigError.BadConfigValue)

    _log.debug("_read_config_file: %s contributed %s", path, values)
    return Ok(values)


def _env_overrides() -> dict[str, Any]:
    """Collect the TYPANI_* environment overrides that are actually set."""
    values: dict[str, Any] = {}
    for env_name, key in _ENV_KEYS.items():
        raw = os.environ.get(env_name)
        if raw is None:
            continue
        values[key] = (
            [part for part in (p.strip() for p in raw.split(",")) if part]
            if key in _LIST_KEYS
            else raw
        )
        _log.debug("_env_overrides: %s set %s=%r", env_name, key, values[key])
    return values
