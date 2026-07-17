from __future__ import annotations

from typing import Callable, Final, Generic, Optional, TypeVar, cast, final

from typani.unit import Unit

T = TypeVar("T")
V = TypeVar("V")


# noinspection PyPep8Naming
@final
class _SOME_UNIT(Unit): ...


_SOME_SENTINEL: Final[_SOME_UNIT] = _SOME_UNIT()


# frob:doc docs/option.md#option
class Option(Generic[T]):
    """An optional value: either :func:`Some` (a present value) or :func:`Nothing`.

    ``Option[T]`` is the explicit, composable alternative to bare ``T | None``.
    Unlike ``Optional[T]``, which is a type alias, ``Option[T]`` is a real
    container with a full transformation API.

    Operator shortcuts::

        option | func    # alias for option.map(func)
        option >> func   # alias for option.and_then(func)
    """

    def __init__(self, *, value: T | _SOME_UNIT = _SOME_SENTINEL) -> None:
        """Construct an Option.  Prefer :func:`Some` / :func:`Nothing` instead."""
        self._value: Final[T | _SOME_UNIT] = value

    @property
    def is_some(self) -> bool:
        """``True`` when a value is present."""
        return not isinstance(self._value, _SOME_UNIT)

    @property
    def is_nothing(self) -> bool:
        """``True`` when no value is present."""
        return isinstance(self._value, _SOME_UNIT)

    @property
    def some(self) -> Optional[T]:
        """The inner value, or ``None``."""
        # noinspection PyUnnecessaryCast
        return cast(T, self._value) if self.is_some else None

    @property
    def danger_some(self) -> T:
        """The inner value; asserts ``is_some`` and crashes on ``Nothing``."""
        assert self.is_some
        # noinspection PyUnnecessaryCast
        return cast(T, self._value)

    def map(self, func: Callable[[T], V]) -> Option[V]:
        """Apply *func* to the value if present; pass ``Nothing`` through unchanged."""
        if self.is_nothing:
            # noinspection PyUnnecessaryCast
            return cast(Option[V], self)
        # noinspection PyUnnecessaryCast
        return Option(value=func(cast(T, self._value)))

    def and_then(self, func: Callable[[T], Option[V]]) -> Option[V]:
        """Chain a computation that may itself return ``Nothing``.

        If ``self`` is ``Nothing``, returns ``Nothing`` without calling *func*.
        """
        if self.is_nothing:
            # noinspection PyUnnecessaryCast
            return cast(Option[V], self)
        # noinspection PyUnnecessaryCast
        return func(cast(T, self._value))

    def or_else(self, func: Callable[[], Option[T]]) -> Option[T]:
        """Return *func()* when the value is absent; return ``self`` when present."""
        if self.is_some:
            return self
        return func()

    def inspect(self, func: Callable[[T], None]) -> Option[T]:
        """Call *func* with the value for side effects; return ``self`` unchanged."""
        if self.is_some:
            # noinspection PyUnnecessaryCast
            func(cast(T, self._value))
        return self

    def unwrap_or(self, default: T) -> T:
        """Return the value if present, otherwise return *default*."""
        # noinspection PyUnnecessaryCast
        return cast(T, self._value) if self.is_some else default

    def __or__(self, func: Callable[[T], V]) -> Option[V]:
        """Alias for :meth:`map`.  ``option | func`` transforms the present value."""
        return self.map(func)

    def __rshift__(self, func: Callable[[T], Option[V]]) -> Option[V]:
        """Alias for :meth:`and_then`.  ``option >> func`` chains an optional computation."""
        return self.and_then(func)

    def __repr__(self) -> str:
        if self.is_some:
            return f"Some({repr(self.danger_some)})"
        return "Nothing"

    def __str__(self) -> str:
        if self.is_some:
            return f"Some({str(self.danger_some)})"
        return "Nothing"


# noinspection PyPep8Naming
# frob:doc docs/option.md#constructors
def Some(value: T, /) -> Option[T]:
    """Construct a present :class:`Option` wrapping *value*."""
    return Option(value=value)


# noinspection PyPep8Naming
# frob:doc docs/option.md#constructors
def Nothing() -> Option[T]:
    """Construct an absent :class:`Option`."""
    # noinspection PyUnnecessaryCast
    return cast(Option[T], Option())
