"""Level-splitting filter that keeps warnings and errors off stdout."""

from __future__ import annotations

import logging


# frob:doc docs/logging.md#logging-config
# frob:tests tests/test_cli.py::test_configure_is_idempotent_and_root_safe
# frob:ticket T-0037
class BelowLevelFilter(logging.Filter):
    """Pass records strictly below ``below``, so stdout never carries WARNING+."""

    def __init__(self, below: str) -> None:
        """Bind the exclusive upper level bound by name (e.g. ``"WARNING"``)."""
        super().__init__()
        # getLevelName, not getattr(logging, ...): a name->number lookup through
        # the logging module's own table, with no dynamic attribute access.
        self._below = logging.getLevelName(below.upper())

    # frob:waive WIRE001 reason="stdlib handler hook" follow_up="T-0038"
    def filter(self, record: logging.LogRecord) -> bool:
        """Return True when the record is strictly below the bound."""
        return record.levelno < self._below
