from __future__ import annotations

import weakref
from enum import Enum, EnumMeta
from typing import Any

# Cache merged sets so A | B and B | A return the identical class object.
# Keyed by frozenset of leaf ErrorSet classes (not intermediate merges).
_merge_cache: dict[frozenset[type], type[ErrorSet]] = {}

# Tracks which leaf sets compose a merged ErrorSet (for flattening on re-merge).
_source_map: weakref.WeakKeyDictionary[type, frozenset[type]] = (
    weakref.WeakKeyDictionary()
)


def _leaves(s: type[ErrorSet]) -> frozenset[type]:
    """Return the leaf ErrorSet classes that make up *s*."""
    return _source_map.get(s, frozenset({s}))


class _ErrorSetMeta(EnumMeta):
    """Metaclass for ErrorSet.

    Adds the ``|`` operator at the class level so that two error-set classes
    can be merged into a new one::

        AllErrors = NetworkError | ParseError

    The result is cached so ``NetworkError | ParseError`` and
    ``ParseError | NetworkError`` return the exact same class object.
    Chains flatten correctly: ``(A | B) | C`` is the same as ``A | B | C``.
    """

    def __or__(cls, other: Any) -> type[ErrorSet]:
        """Return a cached, canonical merge of *cls* and *other*."""
        if not (isinstance(other, type) and issubclass(other, ErrorSet)):
            return NotImplemented
        key: frozenset[type] = _leaves(cls) | _leaves(other)  # type: ignore[arg-type]
        if key in _merge_cache:
            return _merge_cache[key]
        # Sort by class name for a stable, human-readable result name.
        sorted_sets: list[type[ErrorSet]] = sorted(key, key=lambda s: s.__name__)
        name = "_".join(s.__name__ for s in sorted_sets)
        result = merge(*sorted_sets, name=name)
        _source_map[result] = key
        _merge_cache[key] = result
        return result


# frob:doc docs/error_set.md#errorset
# frob:ticket T-0003
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

    # frob:doc docs/error_set.md#accessing-descriptions
    @property
    def description(self) -> str:
        """Human-readable description assigned at definition time."""
        return str(self.value)

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


# frob:doc docs/error_set.md#global--merged-error-sets
def merge(*sets: type[ErrorSet], name: str = "MergedErrorSet") -> type[ErrorSet]:
    """Return a new :class:`ErrorSet` that is the union of all given sets.

    Prefer the ``|`` operator for two-set merges -- it is cached and
    commutative (``A | B`` is the same object as ``B | A``)::

        AllErrors = NetworkError | ParseError

    Use ``merge`` directly when you need a custom name or are merging more
    than two sets at once::

        AllErrors = merge(NetworkError, ParseError, AuthError, name="AllErrors")

    Raises ``ValueError`` if any error name appears in more than one input set.
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
    return ErrorSet(name, members)  # type: ignore[call-arg,return-value]
