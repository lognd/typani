from __future__ import annotations

from enum import Enum, EnumMeta
from typing import Any


class _ErrorSetMeta(EnumMeta):
    """Metaclass for ErrorSet.

    Adds the ``|`` operator at the class level so that two error-set classes
    can be merged into a new one: ``NetworkError | ParseError``.
    """

    def __or__(cls, other: Any) -> type[ErrorSet]:  # type: ignore[override]
        """Return a new ErrorSet that is the union of *cls* and *other*."""
        if not (isinstance(other, type) and issubclass(other, ErrorSet)):
            return NotImplemented  # type: ignore[return-value]
        return merge(cls, other)  # type: ignore[arg-type]


class ErrorSet(Enum, metaclass=_ErrorSetMeta):
    """Zig-inspired typed error enum where each member carries a human-readable description.

    Define an error set by subclassing and assigning string descriptions as values::

        class NetworkError(ErrorSet):
            Timeout = "Connection timed out after the deadline"
            Refused = "Remote host actively refused the connection"

    Each member exposes ``.description`` and formats cleanly via ``str``/``repr``.
    Designed for use as the error type in ``Result[T, MyErrorSet]``.

    Error sets can be merged with ``|`` at the class level::

        AllErrors = NetworkError | ParseError

    **Why not StrEnum?**

    ``enum.StrEnum`` (added in Python 3.11) makes each member compare equal to its
    string value (``NetworkError.Timeout == "Timeout"``).  This is convenient for
    serialisation but creates a footgun: errors silently compare equal to arbitrary
    strings, making exhaustiveness checking unreliable and blurring the boundary
    between the error domain and raw data.

    ``ErrorSet`` keeps values as plain strings *internally* (for the description) but
    never makes members equal to those strings.  Identity and enum-level equality are
    the only comparisons that work, which is what you want when errors are domain
    values, not serialisation tokens.

    **Python 3.10 compatibility**

    ``StrEnum`` requires Python 3.11+.  ``ErrorSet`` is built on the plain
    ``enum.Enum`` API that has been stable since Python 3.4, so it works on
    Python 3.10 and up without any compatibility shims.
    """

    @property
    def description(self) -> str:
        """Human-readable description assigned at definition time."""
        return str(self.value)

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


def merge(*sets: type[ErrorSet], name: str = "MergedErrorSet") -> type[ErrorSet]:
    """Return a new :class:`ErrorSet` that is the union of all given sets.

    Raises ``ValueError`` if any error name appears in more than one of the
    given sets -- Zig's error sets have the same constraint.

    Example::

        from typani.error_set import merge

        AllErrors = merge(NetworkError, ParseError, name="AllErrors")
        AllErrors.Timeout.description  # works
        AllErrors.InvalidJson.description  # also works

    You can also use the ``|`` operator directly on the classes::

        AllErrors = NetworkError | ParseError
    """
    members: dict[str, str] = {}
    for s in sets:
        for member in s:
            if member.name in members:
                raise ValueError(
                    f"merge: duplicate error name {member.name!r} "
                    f"(first seen in a previous set)"
                )
            members[member.name] = str(member.value)
    return ErrorSet(name, members)  # type: ignore[return-value]
