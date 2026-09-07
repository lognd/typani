"""Level-name resolution, in one place, for every module that accepts one.

`logging.getLevelName` looks like the obvious lookup, but its `str -> int`
direction is a deprecated overload -- typeshed marks it "considered a
mistake", so `ty` reports it and it leaks `Any` into whatever it is
assigned to, which `mypy --strict` then flags in turn (T-0039). The
mapping typani actually accepts is small and fixed, so it is spelled out
here rather than looked up: `logging.getLevelNamesMapping()` is 3.11+,
and typani supports 3.10.
"""

from __future__ import annotations

import logging

# frob:doc docs/logging.md#resolve_level
# frob:tests tests/test_cli.py::test_resolve_level_accepts_the_standard_names
# frob:ticket T-0039
#: The level names typani's `--log-level`, `TYPANI_LOG_LEVEL` and
#: `[tool.typani] log_level` accept. Deliberately the stdlib's own standard
#: set and nothing more: a name an application registered with
#: `logging.addLevelName` is not part of typani's CLI contract.
LEVEL_NAMES: dict[str, int] = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


# frob:doc docs/logging.md#resolve_level
# frob:tests tests/test_cli.py::test_resolve_level_accepts_the_standard_names
# frob:ticket T-0039
def resolve_level(name: str) -> int | None:
    """Return the numeric level for a level name, or None if it is not one.

    Case-insensitive. Returning None rather than raising is what lets each
    caller report a bad level in its own idiom -- `ConfigError.BadLogLevel`
    from the config layer, a warning-and-ignore from `configure`.
    """
    return LEVEL_NAMES.get(name.upper())
