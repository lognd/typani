"""Backend selection and native/pure parity tests (T-0010).

Covers: `TYPANI_PURE` forcing pure-Python, version-skew fallback with a
WARNING, and a table-driven parity check between the native extension and
the pure-Python implementation (tests/parity/).
"""

from __future__ import annotations

import importlib
import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest

import typani
import typani._impl as _impl

PARITY_DIR = Path(__file__).parent / "parity"


# frob:tests src/typani/_impl.py::native_active
def test_backend_matches_typani_pure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """`native_active()`/`backend_name()` reflect the process's `TYPANI_PURE` state."""
    if _impl.native_active():
        assert typani.backend_name() == "native"
    else:
        assert typani.backend_name() == "pure"


# frob:tests src/typani/_impl.py::_detect_backend
def test_typani_pure_env_forces_pure_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setting `TYPANI_PURE=1` and reloading `_impl` always selects pure."""
    monkeypatch.setenv("TYPANI_PURE", "1")
    importlib.reload(_impl)
    try:
        assert _impl.backend_name() == "pure"
        assert _impl.native_active() is False
    finally:
        importlib.reload(_impl)


# frob:tests src/typani/_impl.py::_detect_backend
def test_version_skew_falls_back_to_pure_with_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A `typani_core` with a mismatched `__version__` logs a WARNING and falls back."""
    import types

    fake = types.ModuleType("typani_core")
    fake.__version__ = "999.999.999"  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "typani_core", fake)
        mp.delenv("TYPANI_PURE", raising=False)
        with caplog.at_level(logging.WARNING, logger="typani._impl"):
            importlib.reload(_impl)
        assert _impl.backend_name() == "pure"
        assert any("does not match" in rec.message for rec in caplog.records)
    # Real sys.modules["typani_core"] (or its absence) is restored on
    # exiting the context; resync _impl's cached backend to match.
    importlib.reload(_impl)


def _run_parity(*, pure: bool) -> dict[str, object]:
    """Run tests/parity/run_case.py in a subprocess with the given backend forced."""
    import os

    env = dict(os.environ)
    if pure:
        env["TYPANI_PURE"] = "1"
    else:
        env.pop("TYPANI_PURE", None)
    proc = subprocess.run(
        [sys.executable, "run_case.py"],
        cwd=PARITY_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    result: dict[str, object] = json.loads(proc.stdout)
    return result


# frob:tests tests/parity/cases.py::CASES
def test_native_pure_parity() -> None:
    """Every parity case behaves identically under the native and pure backends."""
    if not _impl.native_active():
        pytest.skip("typani_core not active in this environment; nothing to compare")

    native_report = _run_parity(pure=False)
    pure_report = _run_parity(pure=True)

    assert native_report.keys() == pure_report.keys()
    mismatches = {
        name: (native_report[name], pure_report[name])
        for name in native_report
        if native_report[name] != pure_report[name]
    }
    assert not mismatches, f"native/pure parity mismatches: {mismatches}"
