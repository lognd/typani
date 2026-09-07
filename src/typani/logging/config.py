"""The dictConfig payload for typani's logging channel.

A Python dict rather than the usual sibling-repo ``config.toml``: typani
supports 3.10, where ``tomllib`` does not exist, and its runtime
dependency list is empty by contract -- so it cannot reach for ``tomli``
just to read its own logging config. dictConfig's native format is a
dict anyway, so this is the same single source of truth in the format
the stdlib consumes.
"""

from __future__ import annotations

from typing import Any

from typani.logging.filter import BelowLevelFilter
from typani.logging.formatter import TypaniFormatter

# frob:doc docs/logging.md#logging-config
# frob:ticket T-0037
#: The `"()"` values are the classes themselves, not dotted-path strings:
#: dictConfig accepts either, and passing the objects keeps the wiring a real,
#: statically visible reference instead of a name only resolved at runtime.
#: Handlers split by level: DEBUG/INFO to stdout, WARNING+ to stderr, so a
#: `--json` scan's machine-readable stdout is never polluted by diagnostics.
#: Only the `typani` logger is configured (never the root logger) -- see
#: typani.logging.configure for why.
LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "below_warning": {
            "()": BelowLevelFilter,
            "below": "WARNING",
        },
    },
    "formatters": {
        "stdout_fmt": {"()": TypaniFormatter},
        "stderr_fmt": {
            "()": TypaniFormatter,
            "show_level": True,
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "stdout_fmt",
            "stream": "ext://sys.stdout",
            "level": "DEBUG",
            "filters": ["below_warning"],
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "formatter": "stderr_fmt",
            "stream": "ext://sys.stderr",
            "level": "WARNING",
        },
    },
    "loggers": {
        "typani": {
            "level": "WARNING",
            "handlers": ["stdout", "stderr"],
            "propagate": False,
        },
    },
}
