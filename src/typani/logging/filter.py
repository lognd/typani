"""Level-splitting filter that keeps warnings and errors off stdout."""

from __future__ import annotations

import logging

from typani.logging.levels import resolve_level


# frob:doc docs/logging.md#logging-config
# frob:tests tests/test_cli.py::test_configure_is_idempotent_and_root_safe
# frob:ticket T-0037
class BelowLevelFilter(logging.Filter):
    """Pass records strictly below ``below``, so stdout never carries WARNING+."""

    def __init__(self, below: str) -> None:
        """Bind the exclusive upper level bound by name (e.g. ``"WARNING"``)."""
        super().__init__()
        # resolve_level, not getattr(logging, ...) or the deprecated
        # getLevelName str overload: a plain dict lookup that stays typed.
        level = resolve_level(below)
        if level is None:
            raise ValueError(f"not a logging level name: {below!r}")
        self._below = level

    # frob:waive WIRE001 reason="stdlib handler hook" follow_up="T-0038"
    def filter(self, record: logging.LogRecord) -> bool:
        """Return True when the record is strictly below the bound."""
        return record.levelno < self._below
