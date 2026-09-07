"""The central logging channel: get_logger for every module, configure for the CLI.

Deliberately split in two, which is where typani departs from the sibling
CLI repos' `get_logger`-also-initializes pattern: typani is a LIBRARY
first. A library that runs ``logging.dictConfig`` at import time hijacks
its consumer's logging setup, so ``get_logger`` here only names the
logger and attaches nothing. ``configure`` -- which installs handlers,
and only ever on the ``typani`` logger, never the root -- is called
exclusively from the CLI entry point in ``typani.__main__``, where typani
IS the application and owns its own output.
"""

from __future__ import annotations

import logging
import logging.config

from typani.logging.config import LOGGING_CONFIG

_ROOT_LOGGER_NAME = "typani"

_configured = False


# frob:doc docs/logging.md#get_logger
# frob:tests tests/test_cli.py::test_get_logger_attaches_nothing
# frob:ticket T-0037
def get_logger(name: str) -> logging.Logger:
    """Return typani's logger for `name`; attaches no handlers (library-safe)."""
    return logging.getLogger(name)


# frob:doc docs/logging.md#configure
# frob:tests tests/test_cli.py::test_configure_is_idempotent_and_root_safe
# frob:ticket T-0037
def configure(level: str | None = None) -> None:
    """Install typani's handlers on the `typani` logger; idempotent, CLI-only.

    `level` overrides the configured default (WARNING) for the `typani`
    logger only. Repeat calls re-apply just the level, so a second call
    cannot stack duplicate handlers onto the same logger. An unrecognized
    level is warned about and ignored rather than raised: this runs before
    the config layer has had a chance to report it as a ConfigError, and a
    bad `--log-level` must not become a traceback.
    """
    global _configured
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    if not _configured:
        logging.config.dictConfig(LOGGING_CONFIG)
        _configured = True
        logger.debug("configure: typani logging channel installed")
    if level is None:
        return
    resolved = level.upper()
    if not isinstance(logging.getLevelName(resolved), int):
        logger.warning("configure: ignoring unknown log level %r", level)
        return
    logger.setLevel(resolved)
    logger.debug("configure: typani log level set to %s", resolved)
