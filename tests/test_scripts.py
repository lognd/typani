"""Exercise scripts/clean.py, build.py, release.py, and develop.py by path.

Loaded via importlib like tests/test_bump_version.py, since scripts/ is
not a package. Each test operates against tmp_path or monkeypatched
subprocess calls so nothing touches the real repo, git, or the network.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _load_module(name: str) -> ModuleType:
    """Load a scripts/<name>.py module fresh by file path."""
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# frob:tests scripts/clean.py::_remove
def test_clean_removes_fixture_dirs_and_files(tmp_path: Path) -> None:
    _load_module("_common")
    clean = _load_module("clean")

    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "typani-0.1.0.tar.gz").write_text("x")
    (tmp_path / "build").mkdir()
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / "coverage.xml").write_text("x")
    (tmp_path / ".coverage").write_text("x")

    pycache = tmp_path / "src" / "typani" / "__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "mod.pyc").write_text("x")

    egg_info = tmp_path / "src" / "typani.egg-info"
    egg_info.mkdir(parents=True)

    venv_pycache = tmp_path / ".venv" / "lib" / "__pycache__"
    venv_pycache.mkdir(parents=True)

    sys.argv = ["clean.py"]
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(clean, "repo_root", lambda: tmp_path)
        clean.main()

    assert not (tmp_path / "dist").exists()
    assert not (tmp_path / "build").exists()
    assert not (tmp_path / ".pytest_cache").exists()
    assert not (tmp_path / "coverage.xml").exists()
    assert not (tmp_path / ".coverage").exists()
    assert not pycache.exists()
    assert not egg_info.exists()
    assert venv_pycache.exists()  # .venv is skipped


# frob:tests scripts/build.py::main
def test_build_dry_run_prints_uv_build_without_executing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _load_module("_common")
    build = _load_module("build")

    calls: list[list[str]] = []

    def fake_subprocess_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(subprocess, "run", fake_subprocess_run)
        mp.setattr(build, "repo_root", lambda: tmp_path)
        mp.setattr(sys, "argv", ["build.py", "--dry-run"])
        with caplog.at_level("INFO"):
            build.main()

    assert calls == []  # dry run never invokes subprocess.run
    assert "uv build" in caplog.text


# frob:tests scripts/release.py::_refuse_if_dirty
def test_release_refuses_on_dirty_tree(tmp_path: Path) -> None:
    release = _load_module("release")

    def fake_status(root: Path) -> str:
        return " M pyproject.toml\n"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(release, "_git_status_porcelain", fake_status)
        with pytest.raises(SystemExit) as excinfo:
            release._refuse_if_dirty(tmp_path, allow_dirty=False)
        assert excinfo.value.code == 1


# frob:tests scripts/release.py::_refuse_if_dirty
def test_release_allow_dirty_bypasses_refusal(tmp_path: Path) -> None:
    release = _load_module("release")

    def fake_status(root: Path) -> str:
        return " M pyproject.toml\n"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(release, "_git_status_porcelain", fake_status)
        release._refuse_if_dirty(tmp_path, allow_dirty=True)  # does not raise


# frob:tests scripts/release.py::_resolve_publish_token
def test_release_refuses_publish_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    release = _load_module("release")
    monkeypatch.delenv("UV_PUBLISH_TOKEN", raising=False)
    with pytest.raises(SystemExit) as excinfo:
        release._resolve_publish_token()
    assert excinfo.value.code == 1


# frob:tests scripts/release.py::_publish
def test_release_dry_run_never_prints_token(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    release = _load_module("release")
    fake_token = "pypi-FAKE-TOKEN-VALUE"
    monkeypatch.setenv("UV_PUBLISH_TOKEN", fake_token)

    release._publish(tmp_path, dry_run=True)

    captured = capsys.readouterr()
    assert fake_token not in captured.out
    assert fake_token not in captured.err


# frob:tests scripts/develop.py::main
def test_develop_exits_zero_with_warning_when_manifest_missing(
    tmp_path: Path,
) -> None:
    develop = _load_module("develop")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(develop, "repo_root", lambda: tmp_path)
        mp.setattr(sys, "argv", ["develop.py"])
        with pytest.raises(SystemExit) as excinfo:
            develop.main()
        assert excinfo.value.code == 0
