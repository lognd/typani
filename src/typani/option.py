from __future__ import annotations

import copy as _copy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterator,
    TypeVar,
    final,
)

from typani._exceptions import UnwrapError

if TYPE_CHECKING:
    from typani.result import Result

T_co = TypeVar("T_co", covariant=True)
U = TypeVar("U")
V = TypeVar("V")
E = TypeVar("E")

_SOME_MARKER = 0
_NOTHING_MARKER = 1


# frob:doc docs/option.md#option
# frob:ticket T-0009
class Option(Generic[T_co]):
    """An optional value: either :class:`Some` (a present value) or :class:`Nothing`.

    ``Option[T]`` is the explicit, composable alternative to bare ``T | None``.
    Abstract base of :class:`Some` and :class:`Nothing`; not directly
    constructible. ``match o: case Some(v): ... case Nothing(): ...`` works.

    Operator shortcuts::

        option | func    # alias for option.map(func)
        option >> func   # alias for option.and_then(func)
    """

    __slots__ = ()

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Forbid direct construction; ``Some``/``Nothing`` override, never call."""
        raise TypeError("Option is abstract; construct Some(value) or Nothing()")

    @classmethod
    def from_optional(cls, x: T_co | None) -> "Option[T_co]":
        """Wrap ``T | None``: ``Some(x)`` when not ``None``, else ``Nothing()``."""
        # frob:doc docs/option.md#from_optionalx---optiont
        return Nothing() if x is None else Some(x)

    @property
    def is_some(self) -> bool:
        """``True`` when a value is present."""
        raise NotImplementedError

    @property
    def is_nothing(self) -> bool:
        """``True`` when no value is present."""
        raise NotImplementedError

    @property
    def some(self) -> T_co | None:
        """The inner value, or ``None``."""
        raise NotImplementedError

    @property
    def danger_some(self) -> T_co:
        """The inner value; raises ``UnwrapError`` on ``Nothing``."""
        raise NotImplementedError

    def unwrap(self) -> T_co:
        """Return the value; raise ``UnwrapError(self)`` on ``Nothing``."""
        raise NotImplementedError

    def unwrap_or(self, default: U) -> T_co | U:
        """Return the value if present, otherwise return *default*."""
        # frob:doc docs/option.md#unwrap_ordefault---t
        raise NotImplementedError

    def unwrap_or_else(self, fn: Callable[[], U]) -> T_co | U:
        """Return the value if present, otherwise return ``fn()``."""
        raise NotImplementedError

    def expect(self, msg: str) -> T_co:
        """Like :meth:`unwrap`, prefixing the ``UnwrapError`` message with *msg*."""
        raise NotImplementedError

    def map(self, fn: Callable[[T_co], V]) -> "Option[V]":
        """Apply *fn* to the value if present; pass ``Nothing`` through unchanged."""
        # frob:doc docs/option.md#mapfn---optionv
        if self.is_nothing:
            return self  # type: ignore[return-value]  # ty: ignore[invalid-return-type]
        return Some(fn(self.danger_some))

    def and_then(self, fn: Callable[[T_co], "Option[V]"]) -> "Option[V]":
        """Chain a computation that may itself return ``Nothing``."""
        # frob:doc docs/option.md#and_thenfn---optionv
        if self.is_nothing:
            return self  # type: ignore[return-value]  # ty: ignore[invalid-return-type]
        return fn(self.danger_some)

    def or_else(self, fn: Callable[[], "Option[T_co]"]) -> "Option[T_co]":
        """Return *fn()* when the value is absent; return ``self`` when present."""
        # frob:doc docs/option.md#or_elsefn---optiont
        if self.is_some:
            return self
        return fn()

    def inspect(self, fn: Callable[[T_co], None]) -> "Option[T_co]":
        """Call *fn* with the value for side effects; return ``self`` unchanged."""
        # frob:doc docs/option.md#inspectfn---optiont
        raise NotImplementedError

    def filter(self, pred: Callable[[T_co], bool]) -> "Option[T_co]":
        """Keep the value when *pred* holds; a rejected value becomes ``Nothing``."""
        # frob:doc docs/option.md#filterpred---optiont
        if self.is_some and pred(self.danger_some):
            return self
        return Nothing()

    def ok_or(self, err: E) -> "Result[T_co, E]":
        """Convert to a :class:`Result`: ``Some->Ok``, ``Nothing->Err(err)``."""
        # frob:doc docs/option.md#ok_orerr---resultt-e
        # Local import: avoids a module-level cycle with typani.result.
        from typani.result import Err, Ok

        return Ok(self.danger_some) if self.is_some else Err(err)

    def ok_or_else(self, fn: Callable[[], E]) -> "Result[T_co, E]":
        """Like :meth:`ok_or`, computing the error lazily via ``fn()``."""
        # frob:doc docs/option.md#ok_or_elsefn---resultt-e
        from typani.result import Err, Ok

        return Ok(self.danger_some) if self.is_some else Err(fn())

    def __or__(self, fn: Callable[[T_co], V]) -> "Option[V]":
        """Alias for :meth:`map`. ``option | fn`` transforms the present value."""
        return self.map(fn)

    def __rshift__(self, fn: Callable[[T_co], "Option[V]"]) -> "Option[V]":
        """Alias for :meth:`and_then`. ``option >> fn`` chains an optional step."""
        return self.and_then(fn)

    def __iter__(self) -> Iterator[T_co]:
        """Yield the value once for ``Some``; yield nothing for ``Nothing``."""
        if self.is_some:
            yield self.danger_some

    def __bool__(self) -> bool:
        """Always raises: truthiness of an ``Option`` is a common bug, not a query."""
        raise TypeError("Option has no truth value; use is_some/is_nothing or match")

    def __copy__(self) -> "Option[T_co]":
        """Return ``self``: an ``Option`` is immutable, so a shallow copy is a no-op."""
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> "Option[T_co]":
        """Return a new instance with a deep-copied payload."""
        raise NotImplementedError


# frob:doc docs/option.md#constructors
# frob:ticket T-0009
@final
class Some(Option[T_co]):
    """The present variant of :class:`Option`, wrapping a value of type ``T``."""

    __slots__ = ("_value",)
    __match_args__ = ("value",)

    def __init__(self, value: T_co, /) -> None:
        """Wrap *value* as a present option."""
        self._value = value

    @property
    def value(self) -> T_co:
        """The wrapped value (also exposed via ``danger_some``)."""
        return self._value

    @property
    def is_some(self) -> bool:
        """Always ``True`` for ``Some``."""
        return True

    @property
    def is_nothing(self) -> bool:
        """Always ``False`` for ``Some``."""
        return False

    @property
    def some(self) -> T_co:
        """The wrapped value."""
        return self._value

    @property
    def danger_some(self) -> T_co:
        """The wrapped value."""
        return self._value

    def unwrap(self) -> T_co:
        """Return the wrapped value."""
        return self._value

    def unwrap_or(self, default: U) -> T_co | U:
        """Return the wrapped value; *default* is never used."""
        return self._value

    def unwrap_or_else(self, fn: Callable[[], U]) -> T_co | U:
        """Return the wrapped value; *fn* is never called."""
        return self._value

    def expect(self, msg: str) -> T_co:
        """Return the wrapped value; *msg* is never used."""
        return self._value

    def inspect(self, fn: Callable[[T_co], None]) -> "Some[T_co]":
        """Call *fn* with the wrapped value for side effects; return ``self``."""
        fn(self._value)
        return self

    def __eq__(self, other: object) -> bool:
        """Equal to another ``Some`` with an equal payload."""
        if not isinstance(other, Some):
            return NotImplemented
        return bool(self._value == other._value)

    def __ne__(self, other: object) -> bool:
        """Inverse of :meth:`__eq__`."""
        result = self.__eq__(other)
        if result is NotImplemented:
            return result  # type: ignore[no-any-return]
        return not result

    def __hash__(self) -> int:
        """Hash derived from the variant marker and the wrapped value."""
        return hash((_SOME_MARKER, self._value))

    def __repr__(self) -> str:
        """``Some(<repr of value>)``."""
        return f"Some({self._value!r})"

    def __str__(self) -> str:
        """``Some(<str of value>)``."""
        return f"Some({self._value!s})"

    def __reduce__(self) -> tuple[type["Some[T_co]"], tuple[T_co]]:
        """Pickle support: reconstruct via ``Some(value)``."""
        return (Some, (self._value,))

    def __deepcopy__(self, memo: dict[int, object]) -> "Some[T_co]":
        """Return a new ``Some`` with a deep-copied value."""
        return Some(_copy.deepcopy(self._value, memo))


# frob:doc docs/option.md#constructors
# frob:ticket T-0009
@final
class Nothing(Option[T_co]):
    """The absent variant of :class:`Option`. A single cached instance is shared."""

    __slots__ = ()
    __match_args__ = ()

    _INSTANCE: "Nothing[Any] | None" = None

    def __new__(cls, *args: object, **kwargs: object) -> "Nothing[Any]":
        """Return the single cached ``Nothing`` instance; ``Nothing() is Nothing()``."""
        if Nothing._INSTANCE is None:
            Nothing._INSTANCE = object.__new__(cls)
        return Nothing._INSTANCE

    def __init__(self, *args: object, **kwargs: object) -> None:
        """No-op: ``Nothing`` carries no state; overrides the abstract base's raise."""

    @property
    def is_some(self) -> bool:
        """Always ``False`` for ``Nothing``."""
        return False

    @property
    def is_nothing(self) -> bool:
        """Always ``True`` for ``Nothing``."""
        return True

    @property
    def some(self) -> None:
        """Always ``None`` for ``Nothing``."""
        return None

    @property
    def danger_some(self) -> Any:
        """Always raises ``UnwrapError``: ``Nothing`` carries no value."""
        raise UnwrapError(self)

    def unwrap(self) -> Any:
        """Always raises ``UnwrapError``: ``Nothing`` carries no value."""
        raise UnwrapError(self)

    def unwrap_or(self, default: U) -> U:
        """Return *default*."""
        return default

    def unwrap_or_else(self, fn: Callable[[], U]) -> U:
        """Return ``fn()``."""
        return fn()

    def expect(self, msg: str) -> Any:
        """Always raises ``UnwrapError`` prefixed with *msg*: no value here."""
        raise UnwrapError(self, msg)

    def inspect(self, fn: Callable[[T_co], None]) -> "Nothing[T_co]":
        """No-op: ``Nothing`` has no value to inspect; return ``self``."""
        return self

    def __eq__(self, other: object) -> bool:
        """Equal to the other ``Nothing`` instance (there is only ever one)."""
        if not isinstance(other, Nothing):
            return NotImplemented
        return True

    def __ne__(self, other: object) -> bool:
        """Inverse of :meth:`__eq__`."""
        result = self.__eq__(other)
        if result is NotImplemented:
            return result  # type: ignore[no-any-return]
        return not result

    def __hash__(self) -> int:
        """Hash derived from the variant marker alone."""
        return hash((_NOTHING_MARKER,))

    def __repr__(self) -> str:
        """``"Nothing"``."""
        return "Nothing"

    def __str__(self) -> str:
        """``"Nothing"``."""
        return "Nothing"

    def __reduce__(self) -> tuple[type["Nothing[Any]"], tuple[()]]:
        """Pickle support: reconstruct via ``Nothing()``, the shared instance."""
        return (Nothing, ())

    def __copy__(self) -> "Nothing[T_co]":
        """Return the shared instance."""
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> "Nothing[T_co]":
        """Return the shared instance: ``Nothing`` carries no payload to copy."""
        return self


if not TYPE_CHECKING:
    # T-0010: bind the public names to the native PyO3 classes when the
    # backend selection (typani._impl.native_active) picks native; see the
    # matching block at the bottom of typani/result.py for the rationale.
    from typani._impl import native_active as _native_active

    if _native_active():
        import typani_core as _typani_core

        Option = _typani_core.Option
        Some = _typani_core.Some
        Nothing = _typani_core.Nothing
