"""Backend selection between the native typani_core extension and pure Python (T-0010).

`native_active()` decides, once per process, whether `typani.result` and
`typani.option` bind their public `Result`/`Ok`/`Err`/`Option`/`Some`/
`Nothing` names to the PyO3 extension (crates/typani-core) or to the
pure-Python classes defined alongside it. The decision is cached at
import time (`_NATIVE_ACTIVE`) so every module that checks it agrees.

Selection rules, in order:
1. `TYPANI_PURE` set truthy ("1"/"true"/"yes", case-insensitive) forces
   pure-Python, unconditionally.
2. Otherwise, attempt `import typani_core`. An `ImportError` (extension
   not installed -- the `native` extra was not requested) falls back to
   pure-Python.
3. If importable, `typani_core.__version__` must exactly match typani's
   own `__version__` (src/typani/_version.py). A mismatch is a WARNING
   (skew between an ABI-coupled native extension and the pure-Python
   package it was meant to ship alongside) and falls back to pure-Python
   rather than risk running a native ABI that does not match this
   release.
"""

from __future__ import annotations

import logging
import os

from typani._version import __version__ as _TYPANI_VERSION

_log = logging.getLogger(__name__)

_TRUTHY = frozenset({"1", "true", "yes"})


def _env_forces_pure() -> bool:
    """``True`` when ``TYPANI_PURE`` is set to a truthy value (case-insensitive)."""
    raw = os.environ.get("TYPANI_PURE")
    return raw is not None and raw.strip().lower() in _TRUTHY


def _detect_backend() -> str:
    """Run the selection rules once; returns ``"native"`` or ``"pure"``."""
    if _env_forces_pure():
        _log.debug("TYPANI_PURE set: using pure-Python backend")
        return "pure"

    try:
        import typani_core
    except ImportError:
        _log.debug("typani_core not importable: using pure-Python backend")
        return "pure"

    native_version = getattr(typani_core, "__version__", None)
    if native_version != _TYPANI_VERSION:
        _log.warning(
            "typani_core version %r does not match typani version %r; "
            "falling back to the pure-Python backend",
            native_version,
            _TYPANI_VERSION,
        )
        return "pure"

    _log.debug(
        "typani_core %s matches typani %s: using native backend",
        native_version,
        _TYPANI_VERSION,
    )
    return "native"


_BACKEND: str = _detect_backend()


def native_active() -> bool:
    """``True`` when the native ``typani_core`` extension backs Result/Option."""
    return _BACKEND == "native"


def backend_name() -> str:
    """The active backend's name: ``"native"`` or ``"pure"``."""
    return _BACKEND
