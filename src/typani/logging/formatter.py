"""The one formatter every typani log line goes through."""

from __future__ import annotations

import logging


# frob:doc docs/logging.md#logging-config
# frob:tests tests/test_cli.py::test_configure_is_idempotent_and_root_safe
# frob:ticket T-0037
class TypaniFormatter(logging.Formatter):
    """Plain formatter; WARNING+ prefixes the level name, DEBUG/INFO print bare."""

    def __init__(self, show_level: bool = False) -> None:
        """Bind whether this handler's records always carry a level prefix."""
        super().__init__()
        self._show_level = show_level

    # frob:waive WIRE001 reason="stdlib handler hook" follow_up="T-0038"
    def format(self, record: logging.LogRecord) -> str:
        """Render one record: 'LEVEL: message' for WARNING+, bare message below it."""
        msg = record.getMessage()
        if record.exc_info:
            msg = f"{msg}\n{self.formatException(record.exc_info)}"
        if self._show_level or record.levelno >= logging.WARNING:
            return f"{record.levelname}: {msg}"
        return msg
