from __future__ import annotations

import inspect
from typing import final

from typani.unit import Unit


# frob:doc docs/unreachable.md#usage
@final
class Unreachable(Unit):
    """Sentinel that raises ``TypeError`` the moment it is instantiated.

    Use it at code paths that are statically unreachable to make violations
    loud and location-aware at runtime::

        from typani.unreachable import Unreachable
        from typing import assert_never

        def handle(value: int | str) -> str:
            if isinstance(value, int):
                return str(value)
            elif isinstance(value, str):
                return value
            else:
                assert_never(value)
                Unreachable()  # TypeError fires inside __new__; raise is redundant

    The ``TypeError`` message includes the source file, line number, and
    function name of the call site so that accidental instantiations are
    easy to track down.
    """

    def __new__(cls) -> Unreachable:
        frame = inspect.currentframe()
        try:
            caller = frame.f_back if frame is not None else None

            if caller is None:
                location = "unknown location"
            else:
                info = inspect.getframeinfo(caller)
                location = f"{info.filename}:{info.lineno} in {info.function}()"

            raise TypeError(
                f"`UNREACHABLE` was instantiated at {location}. "
                f"This sentinel should never be constructed at runtime."
            )
        finally:
            del frame
