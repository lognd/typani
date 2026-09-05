"""Exercise scripts/bump_version.py against a tmp_path copy of the coupled
files (pyproject.toml, src/typani/__init__.py, crates/typani-core/{pyproject.toml,
Cargo.toml}). Loaded by path (importlib) since scripts/ is not a package.

Every assertion checks the exact resulting string, not just presence/shape,
so that arithmetic mutants on the module's path-construction (`/`) and
version-arithmetic (`+ 1`) expressions are actually killed rather than
merely exercised.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "bump_version.py"


def _load_module() -> ModuleType:
    """Load scripts/bump_version.py as a fresh module object by file path."""
    spec = importlib.util.spec_from_file_location("bump_version", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed_project(tmp_path: Path, *, with_crate: bool) -> ModuleType:
    """Write a minimal coupled-file tree under tmp_path and repoint the
    freshly loaded module's path constants at it, so its functions operate
    entirely inside the sandbox instead of this repo's real files."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "typani"\nversion = "0.1.0"\n'
    )

    init_dir = tmp_path / "src" / "typani"
    init_dir.mkdir(parents=True)
    (init_dir / "__init__.py").write_text(
        'from typani.result import Ok\n\n__version__ = "0.1.0"\n'
    )

    crate_dir = tmp_path / "crates" / "typani-core"
    if with_crate:
        crate_dir.mkdir(parents=True)
        (crate_dir / "pyproject.toml").write_text(
            '[project]\nname = "typani-core"\nversion = "0.1.0"\n'
        )
        (crate_dir / "Cargo.toml").write_text(
            '[package]\nname = "typani-core"\nversion = "0.1.0"\n'
        )

    module = _load_module()
    module.ROOT = tmp_path
    module.PYPROJECT = tmp_path / "pyproject.toml"
    module.INIT_PY = tmp_path / "src" / "typani" / "__init__.py"
    module.NATIVE_PYPROJECT = crate_dir / "pyproject.toml"
    module.NATIVE_CARGO_TOML = crate_dir / "Cargo.toml"
    return module


# frob:tests scripts/bump_version.py::_bump
def test_bump_patch_increments_only_patch() -> None:
    module = _load_module()
    assert module._bump("0.1.0", "patch") == "0.1.1"
    assert module._bump("1.2.9", "patch") == "1.2.10"


# frob:tests scripts/bump_version.py::_bump
def test_bump_minor_increments_minor_and_resets_patch() -> None:
    module = _load_module()
    assert module._bump("0.1.5", "minor") == "0.2.0"
    assert module._bump("3.9.9", "minor") == "3.10.0"


# frob:tests scripts/bump_version.py::_bump
def test_bump_major_increments_major_and_resets_minor_patch() -> None:
    module = _load_module()
    assert module._bump("1.2.3", "major") == "2.0.0"
    assert module._bump("9.9.9", "major") == "10.0.0"


# frob:tests scripts/bump_version.py::_read_current_version
def test_read_current_version_reads_exact_string(tmp_path: Path) -> None:
    module = _seed_project(tmp_path, with_crate=False)
    assert module._read_current_version() == "0.1.0"


# frob:tests scripts/bump_version.py::_write_pyproject_version
def test_write_pyproject_version_rewrites_only_version_field(
    tmp_path: Path,
) -> None:
    module = _seed_project(tmp_path, with_crate=False)
    module._write_pyproject_version("0.2.0")
    text = (tmp_path / "pyproject.toml").read_text()
    assert text == '[project]\nname = "typani"\nversion = "0.2.0"\n'


# frob:tests scripts/bump_version.py::_write_init_version
def test_write_init_version_rewrites_only_version_literal(
    tmp_path: Path,
) -> None:
    module = _seed_project(tmp_path, with_crate=False)
    module._write_init_version("0.2.0")
    text = (tmp_path / "src" / "typani" / "__init__.py").read_text()
    assert text == 'from typani.result import Ok\n\n__version__ = "0.2.0"\n'


# frob:tests scripts/bump_version.py::_write_native_pyproject_version
def test_write_native_pyproject_version_rewrites_crate_pyproject(
    tmp_path: Path,
) -> None:
    module = _seed_project(tmp_path, with_crate=True)
    module._write_native_pyproject_version("0.2.0")
    text = (tmp_path / "crates" / "typani-core" / "pyproject.toml").read_text()
    assert text == '[project]\nname = "typani-core"\nversion = "0.2.0"\n'


# frob:tests scripts/bump_version.py::_write_native_pyproject_version
def test_write_native_pyproject_version_noop_when_crate_absent(
    tmp_path: Path,
) -> None:
    module = _seed_project(tmp_path, with_crate=False)
    module._write_native_pyproject_version("0.2.0")
    assert not (tmp_path / "crates" / "typani-core" / "pyproject.toml").exists()


# frob:tests scripts/bump_version.py::_write_cargo_toml_version
def test_write_cargo_toml_version_rewrites_crate_cargo_toml(
    tmp_path: Path,
) -> None:
    module = _seed_project(tmp_path, with_crate=True)
    module._write_cargo_toml_version("0.2.0")
    text = (tmp_path / "crates" / "typani-core" / "Cargo.toml").read_text()
    assert text == '[package]\nname = "typani-core"\nversion = "0.2.0"\n'


# frob:tests scripts/bump_version.py::_write_cargo_toml_version
def test_write_cargo_toml_version_noop_when_crate_absent(tmp_path: Path) -> None:
    module = _seed_project(tmp_path, with_crate=False)
    module._write_cargo_toml_version("0.2.0")
    assert not (tmp_path / "crates" / "typani-core" / "Cargo.toml").exists()


# frob:tests scripts/bump_version.py::main
def test_main_default_part_bumps_patch_across_all_coupled_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _seed_project(tmp_path, with_crate=True)
    monkeypatch.setattr(sys, "argv", ["bump_version.py"])
    module.main()

    out = capsys.readouterr().out.strip()
    assert out == "0.1.1"
    assert (tmp_path / "pyproject.toml").read_text() == (
        '[project]\nname = "typani"\nversion = "0.1.1"\n'
    )
    assert (tmp_path / "src" / "typani" / "__init__.py").read_text() == (
        'from typani.result import Ok\n\n__version__ = "0.1.1"\n'
    )
    assert (
        tmp_path / "crates" / "typani-core" / "pyproject.toml"
    ).read_text() == '[project]\nname = "typani-core"\nversion = "0.1.1"\n'
    assert (
        tmp_path / "crates" / "typani-core" / "Cargo.toml"
    ).read_text() == '[package]\nname = "typani-core"\nversion = "0.1.1"\n'


# frob:tests scripts/bump_version.py::main
def test_main_part_minor_bumps_minor_across_all_coupled_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _seed_project(tmp_path, with_crate=True)
    monkeypatch.setattr(sys, "argv", ["bump_version.py", "--part", "minor"])
    module.main()

    assert capsys.readouterr().out.strip() == "0.2.0"
    assert (tmp_path / "pyproject.toml").read_text() == (
        '[project]\nname = "typani"\nversion = "0.2.0"\n'
    )


# frob:tests scripts/bump_version.py::main
def test_main_part_major_bumps_major_across_all_coupled_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _seed_project(tmp_path, with_crate=True)
    monkeypatch.setattr(sys, "argv", ["bump_version.py", "--part", "major"])
    module.main()

    assert capsys.readouterr().out.strip() == "1.0.0"
    assert (tmp_path / "pyproject.toml").read_text() == (
        '[project]\nname = "typani"\nversion = "1.0.0"\n'
    )


# frob:tests scripts/bump_version.py::main
def test_main_set_writes_exact_explicit_version_to_every_coupled_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _seed_project(tmp_path, with_crate=True)
    monkeypatch.setattr(sys, "argv", ["bump_version.py", "--set", "9.8.7"])
    module.main()

    out = capsys.readouterr().out.strip()
    assert out == "9.8.7"
    assert (tmp_path / "pyproject.toml").read_text() == (
        '[project]\nname = "typani"\nversion = "9.8.7"\n'
    )
    assert (tmp_path / "src" / "typani" / "__init__.py").read_text() == (
        'from typani.result import Ok\n\n__version__ = "9.8.7"\n'
    )
    assert (
        tmp_path / "crates" / "typani-core" / "pyproject.toml"
    ).read_text() == '[project]\nname = "typani-core"\nversion = "9.8.7"\n'
    assert (
        tmp_path / "crates" / "typani-core" / "Cargo.toml"
    ).read_text() == '[package]\nname = "typani-core"\nversion = "9.8.7"\n'


# frob:tests scripts/bump_version.py::main
def test_main_leaves_crate_files_absent_when_crate_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _seed_project(tmp_path, with_crate=False)
    monkeypatch.setattr(sys, "argv", ["bump_version.py"])
    module.main()

    assert capsys.readouterr().out.strip() == "0.1.1"
    assert (tmp_path / "pyproject.toml").read_text() == (
        '[project]\nname = "typani"\nversion = "0.1.1"\n'
    )
    assert not (tmp_path / "crates" / "typani-core" / "pyproject.toml").exists()
    assert not (tmp_path / "crates" / "typani-core" / "Cargo.toml").exists()


# frob:tests scripts/bump_version.py::main
def test_main_set_rejects_malformed_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _seed_project(tmp_path, with_crate=False)
    monkeypatch.setattr(sys, "argv", ["bump_version.py", "--set", "not-a-version"])

    with pytest.raises(SystemExit) as excinfo:
        module.main()
    assert excinfo.value.code == 1

    # The malformed --set is rejected before any file is touched.
    assert (tmp_path / "pyproject.toml").read_text() == (
        '[project]\nname = "typani"\nversion = "0.1.0"\n'
    )
