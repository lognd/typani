from __future__ import annotations

from typing import Callable, Final, Generic, Optional, TypeVar, cast, final

from typani.unit import Unit

T = TypeVar("T")
V = TypeVar("V")
E = TypeVar("E")
F = TypeVar("F")


# noinspection PyPep8Naming
@final
class _OK_UNIT(Unit): ...


# noinspection PyPep8Naming
@final
class _EMPTY_UNIT(Unit): ...


# frob:doc docs/result.md#result
# frob:ticket T-0003
class Result(Generic[T, E]):
    """Rust-inspired ``Result<T, E>``: a value that is either ``Ok(T)`` or ``Err(E)``.

    Exactly one variant must be set at construction time; providing both or
    neither raises ``TypeError``.  Prefer the :func:`Ok` and :func:`Err`
    factory functions over constructing directly.

    Operator shortcuts::

        result | func    # alias for result.map(func)
        result >> func   # alias for result.and_then(func)
    """

    _OK_SINGLETON: Final[_OK_UNIT] = _OK_UNIT()
    _ERR_SINGLETON: Final[_EMPTY_UNIT] = _EMPTY_UNIT()

    def __init__(
        self, *, ok: T | _OK_UNIT = _OK_SINGLETON, err: E | _EMPTY_UNIT = _ERR_SINGLETON
    ) -> None:
        """Construct a Result.  Use :func:`Ok` / :func:`Err` instead."""
        self._ok: Final[T | _OK_UNIT] = ok
        self._err: Final[E | _EMPTY_UNIT] = err
        if self._ok is Result._OK_SINGLETON and self._err is Result._ERR_SINGLETON:
            raise TypeError(
                "There is a `Result` with neither an `ok` option specified or an `err` option specified."
            )
        elif (
            self._ok is not Result._OK_SINGLETON
            and self._err is not Result._ERR_SINGLETON
        ):
            raise TypeError(
                f"There is a `Result` with both an `ok` option (type: `{self._ok.__class__.__name__}`, repr: `{self._ok}`) and an `err` option (type: `{self._err.__class__.__name__}`, repr: `{self._err}`) specified."
            )

    # frob:doc docs/result.md#map-func---resultv-e
    def map(self, func: Callable[[T], V]) -> Result[V, E]:
        """Apply *func* to the success value; pass ``Err`` through unchanged."""
        if self.is_err:
            # cast is safe because invariant is only `err` or `ok` specified.
            # if object `is_err`, then `ok` is empty anyway, and this is safe.
            # noinspection PyUnnecessaryCast
            return cast(Result[V, E], self)
        # cast is safe because `is_err` being false guarantees that `_ok` is valid.
        # noinspection PyUnnecessaryCast
        return Result[V, E](ok=func(cast(T, self._ok)))

    # frob:doc docs/result.md#map_err-func---resultt-f
    def map_err(self, func: Callable[[E], F]) -> Result[T, F]:
        """Apply *func* to the error value; pass ``Ok`` through unchanged."""
        # casts are safe for the same reasons as above.
        if self.is_ok:
            # noinspection PyUnnecessaryCast
            return cast(Result[T, F], self)
        # noinspection PyUnnecessaryCast
        return Result[T, F](err=func(cast(E, self._err)))

    # frob:doc docs/result.md#and_then-func---resultv-e--f
    def and_then(self, func: Callable[[T], Result[V, F]]) -> Result[V, E | F]:
        """Chain a fallible computation; propagate the first error encountered.

        If ``self`` is ``Ok``, calls ``func(value)`` and returns its result.
        If ``self`` or the returned inner result is ``Err``, that error is
        returned and ``func`` is never called.
        """
        result = self.map(func)

        # Lots of casting; couple are "unnecessary", but I do it just to appease
        # any checker in the future that's *really* smart (i.e. no double singletons).
        # Additionally, you can check manually but the invariants of `is_err` and
        # `is_ok` ensures each of the following casts are safe.

        if result.is_err:
            # noinspection PyUnnecessaryCast
            return Result[V, E | F](err=cast(E, result._err))
        # noinspection PyUnnecessaryCast
        ok = cast(Result[V, F], result._ok)
        if ok.is_err:
            # noinspection PyUnnecessaryCast
            return Result[V, E | F](err=cast(F, ok._err))
        # noinspection PyUnnecessaryCast
        return Result[V, E | F](ok=cast(V, ok._ok))

    # frob:doc docs/result.md#or_else-func---resultt-f
    def or_else(self, func: Callable[[E], Result[T, F]]) -> Result[T, F]:
        """Recover from an error by calling *func* with the error value.

        If ``self`` is ``Ok``, returns ``self`` unchanged.
        """
        if self.is_ok:
            # noinspection PyUnnecessaryCast
            return cast(Result[T, F], self)
        # not `is_ok` invariant guarantees `err` cast validity
        # noinspection PyUnnecessaryCast
        return func(cast(E, self.err))

    # frob:doc docs/result.md#inspect-func---resultt-e
    def inspect(self, func: Callable[[T], None]) -> Result[T, E]:
        """Call *func* with the success value for side effects; return ``self`` unchanged."""
        if not self.is_err:
            # cast is safe because invariant is only `err` or `ok` specified.
            # if object `is_err`, then `ok` is empty anyway, and this is safe.
            # noinspection PyUnnecessaryCast
            func(cast(T, self._ok))
        return self

    @property
    def is_ok(self) -> bool:
        """``True`` when this result holds a success value."""
        return self._ok is not Result._OK_SINGLETON

    @property
    def ok(self) -> Optional[T]:
        """The success value, or ``None`` if this is an ``Err``."""
        # cast is safe because `is_ok` guarantees that `_ok` is valid.
        # noinspection PyUnnecessaryCast
        return cast(T, self._ok) if self.is_ok else None

    @property
    def danger_ok(self) -> T:
        """The success value; asserts ``is_ok`` and crashes on ``Err``."""
        assert self.is_ok
        # noinspection PyUnnecessaryCast
        return cast(T, self._ok)

    @property
    def is_err(self) -> bool:
        """``True`` when this result holds an error value."""
        return self._err is not Result._ERR_SINGLETON

    @property
    def err(self) -> Optional[E]:
        """The error value, or ``None`` if this is an ``Ok``."""
        # cast is safe because `is_err` guarantees that `_err` is valid.
        # noinspection PyUnnecessaryCast
        return cast(E, self._err) if self.is_err else None

    @property
    def danger_err(self) -> E:
        """The error value; asserts ``is_err`` and crashes on ``Ok``."""
        assert self.is_err
        # noinspection PyUnnecessaryCast
        return cast(E, self._err)

    # The unused local is used for type-hinting.
    # noinspection PyUnusedLocal
    # frob:doc docs/result.md#swap_err-err_type---resultt-f
    def swap_err(self, err: type[F]) -> Result[T, F]:
        """Assert-cast the error type.  Only valid when ``is_ok``; asserts otherwise."""
        assert self.is_ok
        # noinspection PyUnnecessaryCast
        return cast(Result[T, F], self)

    # The unused local is used for type-hinting.
    # noinspection PyUnusedLocal
    # frob:doc docs/result.md#swap_ok-ok_type---resultv-e
    def swap_ok(self, ok: type[V]) -> Result[V, E]:
        """Assert-cast the success type.  Only valid when ``is_err``; asserts otherwise."""
        assert self.is_err
        # noinspection PyUnnecessaryCast
        return cast(Result[V, E], self)

    def __or__(self, func: Callable[[T], V]) -> Result[V, E]:
        """Alias for :meth:`map`.  ``result | func`` transforms the success value."""
        return self.map(func)

    def __rshift__(self, func: Callable[[T], Result[V, F]]) -> Result[V, E | F]:
        """Alias for :meth:`and_then`.  ``result >> func`` chains a fallible computation."""
        return self.and_then(func)

    def __repr__(self) -> str:
        if self.is_ok:
            return f"Ok({repr(self.danger_ok)})"
        elif self.is_err:
            return f"Err({repr(self.danger_err)})"
        return super().__repr__()

    def __str__(self) -> str:
        if self.is_ok:
            return f"Ok({str(self.danger_ok)})"
        elif self.is_err:
            return f"Err({str(self.danger_err)})"
        return super().__str__()


# noinspection PyPep8Naming
# frob:doc docs/result.md#constructors
def Ok(ok: T, /) -> Result[T, E]:
    """Construct a successful :class:`Result` wrapping *ok*."""
    return Result(ok=ok)


# noinspection PyPep8Naming
# frob:doc docs/result.md#constructors
def Err(err: E, /) -> Result[T, E]:
    """Construct a failed :class:`Result` wrapping *err*."""
    return Result(err=err)
