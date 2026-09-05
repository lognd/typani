from __future__ import annotations

import copy as _copy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterator,
    TypeVar,
    cast,
    final,
)

from typani._exceptions import UnwrapError

if TYPE_CHECKING:
    from typani.option import Option

T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)
U = TypeVar("U")
V = TypeVar("V")
F = TypeVar("F")
# Plain (non-covariant) type vars for `catch`: the classmethod produces a
# fresh Result[T2, E2] rather than reusing the class's covariant T_co/E_co,
# which cannot appear in contravariant (parameter) position.
T2 = TypeVar("T2")
E2 = TypeVar("E2")

_OK_MARKER = 0
_ERR_MARKER = 1


# frob:doc docs/result.md#result
# frob:ticket T-0009
class Result(Generic[T_co, E_co]):
    """Rust-inspired ``Result<T, E>``: a value that is either ``Ok(T)`` or ``Err(E)``.

    Abstract base of :class:`Ok` and :class:`Err`; not directly constructible.
    Prefer ``isinstance(r, Ok)`` / ``isinstance(r, Err)`` narrowing or
    ``match r: case Ok(v): ... case Err(e): ...`` over hand-rolled checks.

    Operator shortcuts::

        result | func    # alias for result.map(func)
        result >> func   # alias for result.and_then(func)
    """

    __slots__ = ()

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Forbid direct construction; ``Ok``/``Err`` override, never call this."""
        raise TypeError("Result is abstract; construct Ok(value) or Err(error)")

    @classmethod
    def catch(
        cls,
        fn: Callable[[], T2],
        *exceptions: type[BaseException],
        on_error: Callable[[BaseException], E2],
    ) -> "Result[T2, E2]":
        """Run *fn*; return ``Ok(fn())``, or ``Err(on_error(exc))`` for a caught exc.

        Defaults to catching ``Exception`` (never ``BaseException``) when no
        *exceptions* are given. This is the single home for the
        exception-to-Result boundary instead of hand-written ``try/except``.
        """
        # frob:doc docs/result.md#catchfn-exceptions-on_error---resultt-e
        caught = exceptions or (Exception,)
        try:
            return Ok(fn())
        except caught as exc:
            return Err(on_error(exc))

    # -- properties implemented per subclass -----------------------------

    @property
    def is_ok(self) -> bool:
        """``True`` when this result holds a success value."""
        raise NotImplementedError

    @property
    def is_err(self) -> bool:
        """``True`` when this result holds an error value."""
        raise NotImplementedError

    @property
    def ok(self) -> T_co | None:
        """The success value, or ``None`` if this is an ``Err``."""
        raise NotImplementedError

    @property
    def err(self) -> E_co | None:
        """The error value, or ``None`` if this is an ``Ok``."""
        raise NotImplementedError

    @property
    def danger_ok(self) -> T_co:
        """The success value; raises ``UnwrapError`` on ``Err``."""
        raise NotImplementedError

    @property
    def danger_err(self) -> E_co:
        """The error value; raises ``UnwrapError`` on ``Ok``."""
        raise NotImplementedError

    @property
    def notes(self) -> tuple[str, ...]:
        """Notes attached via :meth:`note`, oldest first; always ``()`` on ``Ok``."""
        return ()

    @property
    def trace(self) -> tuple[str, ...]:
        """Error-return trace from :meth:`traced`, innermost first; ``()`` on ``Ok``."""
        return ()

    def is_ok_and(self, pred: Callable[[T_co], bool]) -> bool:
        """``True`` when this is ``Ok`` and *pred* holds for its value."""
        raise NotImplementedError

    def is_err_and(self, pred: Callable[[E_co], bool]) -> bool:
        """``True`` when this is ``Err`` and *pred* holds for its error."""
        raise NotImplementedError

    def unwrap(self, *, err: F | None = None, note: str | None = None) -> T_co:
        """Return the success value; raise ``UnwrapError(self)`` on ``Err``.

        With *err* given, an ``Err`` propagates via ``self.wrap_err(err)``
        instead of ``self`` -- i.e. ``r.unwrap(err=E, note=N)`` is exactly
        ``r.wrap_err(E).note(N).unwrap()``, just without the intermediate
        name. *note* alone (no *err*) appends to the existing ``Err``.
        """
        raise NotImplementedError

    def unwrap_err(self) -> E_co:
        """Return the error value; raise ``UnwrapError(self)`` on ``Ok``."""
        raise NotImplementedError

    def unwrap_or(self, default: U) -> T_co | U:
        """Return the success value, or *default* when this is ``Err``."""
        raise NotImplementedError

    def unwrap_or_else(self, fn: Callable[[E_co], U]) -> T_co | U:
        """Return the success value, or ``fn(error)`` when this is ``Err``."""
        raise NotImplementedError

    def expect(self, msg: str) -> T_co:
        """Like :meth:`unwrap`, prefixing the ``UnwrapError`` message with *msg*."""
        raise NotImplementedError

    def expect_err(self, msg: str) -> E_co:
        """Like :meth:`unwrap_err`, prefixing the ``UnwrapError`` message with *msg*."""
        raise NotImplementedError

    def map(self, fn: Callable[[T_co], V]) -> "Result[V, E_co]":
        """Apply *fn* to the success value; pass ``Err`` through unchanged."""
        # frob:doc docs/result.md#mapfn---resultv-e
        if self.is_err:
            return cast("Result[V, E_co]", self)
        return Ok(fn(self.danger_ok))

    def map_err(self, fn: Callable[[E_co], F]) -> "Result[T_co, F]":
        """Apply *fn* to the error value, preserving notes; ``Ok`` passes through."""
        # frob:doc docs/result.md#map_errfn---resultt-f
        if self.is_ok:
            return cast("Result[T_co, F]", self)
        return Err(fn(self.danger_err))._with_meta(self.notes, self.trace)

    def and_then(self, fn: Callable[[T_co], "Result[V, F]"]) -> "Result[V, E_co | F]":
        """Chain a fallible computation; propagate the first error encountered."""
        # frob:doc docs/result.md#and_thenfn---resultv-e--f
        if self.is_err:
            return cast("Result[V, E_co | F]", self)
        return fn(self.danger_ok)

    def or_else(self, fn: Callable[[E_co], "Result[T_co, F]"]) -> "Result[T_co, F]":
        """Recover from an error by calling *fn* with the error value."""
        # frob:doc docs/result.md#or_elsefn---resultt-f
        if self.is_ok:
            return cast("Result[T_co, F]", self)
        return fn(self.danger_err)

    def inspect(self, fn: Callable[[T_co], None]) -> "Result[T_co, E_co]":
        """Call *fn* with the success value for side effects; return ``self``."""
        # frob:doc docs/result.md#inspectfn---resultt-e
        raise NotImplementedError

    def inspect_err(self, fn: Callable[[E_co], None]) -> "Result[T_co, E_co]":
        """Call *fn* with the error value for side effects; return ``self``."""
        # frob:doc docs/result.md#inspect_errfn---resultt-e
        raise NotImplementedError

    def fold(self, on_ok: Callable[[T_co], U], on_err: Callable[[E_co], U]) -> U:
        """Collapse to a single value: ``on_ok(value)`` or ``on_err(error)``."""
        # frob:doc docs/result.md#foldon_ok-on_err---u
        raise NotImplementedError

    def to_option(self) -> "Option[T_co]":
        """Convert to an :class:`Option`: ``Ok->Some``, ``Err->Nothing()``."""
        # frob:doc docs/result.md#to_option---optiont
        raise NotImplementedError

    def note(self, msg: str) -> "Result[T_co, E_co]":
        """Attach context to an ``Err``, leaving its payload alone; ``Ok`` no-ops."""
        # frob:doc docs/result.md#notemsg---resultt-e
        if self.is_ok:
            return self
        return Err(self.danger_err)._with_meta(self.notes + (msg,), self.trace)

    def traced(self, site: str) -> "Result[T_co, E_co]":
        """Append *site* to the error-return trace, innermost first; ``Ok`` no-ops.

        Called by :func:`typani.propagate` on every hop so a chain of
        `@propagate` functions leaves a breadcrumb trail of *where*, not a
        full traceback -- see docs/result.md#return-trace. Costs nothing on
        the happy path: it only ever runs from an already-caught
        ``UnwrapError``.
        """
        # frob:doc docs/result.md#return-trace
        # frob:ticket T-0028
        if self.is_ok:
            return self
        return Err(self.danger_err)._with_meta(self.notes, self.trace + (site,))

    def wrap_err(self, err: F) -> "Result[T_co, F]":
        """Replace an ``Err``'s payload with *err*, noting the original; ``Ok`` no-ops.

        Unlike :meth:`map_err`, *err* is a plain replacement value, not a
        function of the old error -- the old error is not lost, it is
        appended to `.notes` as ``f"caused by {inner!r}"`` so it stays
        inspectable. Existing notes are preserved ahead of that new one.
        """
        # frob:doc docs/result.md#wrap_errerr---resultt-f
        if self.is_ok:
            return cast("Result[T_co, F]", self)
        cause_note = f"caused by {self.danger_err!r}"
        return Err(err)._with_meta(self.notes + (cause_note,), self.trace)

    def swap_err(self, err: type[F]) -> "Result[T_co, F]":
        """Assert-cast the error type. Only valid when ``is_ok``; else raises."""
        # frob:doc docs/result.md#swap_errerr_type---resultt-f
        if self.is_err:
            raise UnwrapError(self)
        return cast("Result[T_co, F]", self)

    def swap_ok(self, ok: type[V]) -> "Result[V, E_co]":
        """Assert-cast the success type. Only valid when ``is_err``; else raises."""
        # frob:doc docs/result.md#swap_okok_type---resultv-e
        if self.is_ok:
            raise UnwrapError(self)
        return cast("Result[V, E_co]", self)

    def __or__(self, fn: Callable[[T_co], V]) -> "Result[V, E_co]":
        """Alias for :meth:`map`. ``result | fn`` transforms the success value."""
        return self.map(fn)

    def __rshift__(self, fn: Callable[[T_co], "Result[V, F]"]) -> "Result[V, E_co | F]":
        """Alias for :meth:`and_then`. ``result >> fn`` chains a fallible step."""
        return self.and_then(fn)

    def __iter__(self) -> Iterator[T_co]:
        """Yield the success value once for ``Ok``; yield nothing for ``Err``."""
        if self.is_ok:
            yield self.danger_ok

    def __bool__(self) -> bool:
        """Always raises: truthiness of a ``Result`` is a common bug, not a query."""
        raise TypeError("Result has no truth value; use is_ok/is_err or match")

    def __copy__(self) -> "Result[T_co, E_co]":
        """Return ``self``: a ``Result`` is immutable, so a shallow copy is a no-op."""
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> "Result[T_co, E_co]":
        """Return a new instance with a deep-copied payload; notes are preserved."""
        raise NotImplementedError


def _rebuild_err(
    error: Any, notes: tuple[str, ...], trace: tuple[str, ...] = ()
) -> "Err[Any, Any]":
    """Reconstruct an ``Err`` with its notes/trace for :func:`pickle.loads`.

    *trace* defaults to ``()`` so pickles written before T-0028's trace
    field (2-arg calls) still unpickle cleanly.
    """
    return Err(error)._with_meta(notes, trace)


# frob:doc docs/result.md#constructors
# frob:ticket T-0009
@final
class Ok(Result[T_co, E_co]):
    """The success variant of :class:`Result`, wrapping a value of type ``T``."""

    __slots__ = ("_value",)
    __match_args__ = ("value",)

    def __init__(self, value: T_co, /) -> None:
        """Wrap *value* as a successful result."""
        self._value = value

    @property
    def value(self) -> T_co:
        """The wrapped success value (also exposed via ``danger_ok``)."""
        return self._value

    @property
    def is_ok(self) -> bool:
        """Always ``True`` for ``Ok``."""
        return True

    @property
    def is_err(self) -> bool:
        """Always ``False`` for ``Ok``."""
        return False

    @property
    def ok(self) -> T_co:
        """The wrapped value."""
        return self._value

    @property
    def err(self) -> None:
        """Always ``None`` for ``Ok``."""
        return None

    @property
    def danger_ok(self) -> T_co:
        """The wrapped value."""
        return self._value

    @property
    def danger_err(self) -> Any:
        """Always raises ``UnwrapError``: ``Ok`` carries no error."""
        raise UnwrapError(self)

    def is_ok_and(self, pred: Callable[[T_co], bool]) -> bool:
        """``True`` when *pred* holds for the wrapped value."""
        return bool(pred(self._value))

    def is_err_and(self, pred: Callable[[E_co], bool]) -> bool:
        """Always ``False``: ``Ok`` has no error to test."""
        return False

    def unwrap(self, *, err: F | None = None, note: str | None = None) -> T_co:
        """Return the wrapped value; *err*/*note* are ignored on ``Ok``."""
        if err is None and note is None:
            return self._value
        return self._value

    def unwrap_err(self) -> E_co:
        """Always raises ``UnwrapError``: ``Ok`` carries no error."""
        raise UnwrapError(self)

    def unwrap_or(self, default: U) -> T_co | U:
        """Return the wrapped value; *default* is never used."""
        return self._value

    def unwrap_or_else(self, fn: Callable[[E_co], U]) -> T_co | U:
        """Return the wrapped value; *fn* is never called."""
        return self._value

    def expect(self, msg: str) -> T_co:
        """Return the wrapped value; *msg* is never used."""
        return self._value

    def expect_err(self, msg: str) -> E_co:
        """Always raises ``UnwrapError`` prefixed with *msg*: no error here."""
        raise UnwrapError(self, msg)

    def inspect(self, fn: Callable[[T_co], None]) -> "Ok[T_co, E_co]":
        """Call *fn* with the wrapped value for side effects; return ``self``."""
        fn(self._value)
        return self

    def inspect_err(self, fn: Callable[[E_co], None]) -> "Ok[T_co, E_co]":
        """No-op: ``Ok`` has no error to inspect; return ``self``."""
        return self

    def fold(self, on_ok: Callable[[T_co], U], on_err: Callable[[E_co], U]) -> U:
        """Return ``on_ok(value)``; *on_err* is never called."""
        return on_ok(self._value)

    def to_option(self) -> "Option[T_co]":
        """Convert to :class:`~typani.option.Some` wrapping the value."""
        # Local import: avoids a module-level cycle with typani.option.
        from typani.option import Some

        return Some(self._value)

    def __eq__(self, other: object) -> bool:
        """Equal to another ``Ok`` with an equal payload; notes are not compared."""
        if not isinstance(other, Ok):
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
        return hash((_OK_MARKER, self._value))

    def __repr__(self) -> str:
        """``Ok(<repr of value>)``."""
        return f"Ok({self._value!r})"

    def __str__(self) -> str:
        """``Ok(<str of value>)``."""
        return f"Ok({self._value!s})"

    def __reduce__(self) -> tuple[type["Ok[T_co, E_co]"], tuple[T_co]]:
        """Pickle support: reconstruct via ``Ok(value)``."""
        return (Ok, (self._value,))

    def __deepcopy__(self, memo: dict[int, object]) -> "Ok[T_co, E_co]":
        """Return a new ``Ok`` with a deep-copied value."""
        return Ok(_copy.deepcopy(self._value, memo))


# frob:doc docs/result.md#constructors
# frob:ticket T-0009
@final
class Err(Result[T_co, E_co]):
    """The failure variant of :class:`Result`, wrapping an error of type ``E``."""

    __slots__ = ("_error", "_notes", "_trace")
    __match_args__ = ("error",)

    def __init__(self, error: E_co, /) -> None:
        """Wrap *error* as a failed result with no notes/trace attached."""
        self._error = error
        self._notes: tuple[str, ...] = ()
        self._trace: tuple[str, ...] = ()

    def _with_meta(
        self, notes: tuple[str, ...], trace: tuple[str, ...] = ()
    ) -> "Err[T_co, E_co]":
        """Return ``self`` with *notes*/*trace* installed.

        Used by note()/map_err()/wrap_err()/traced()/pickling -- the single
        home for mutating a freshly-constructed ``Err``'s metadata.
        """
        self._notes = notes
        self._trace = trace
        return self

    @property
    def error(self) -> E_co:
        """The wrapped error value (also exposed via ``danger_err``)."""
        return self._error

    @property
    def notes(self) -> tuple[str, ...]:
        """Notes attached via :meth:`Result.note`, oldest first."""
        return self._notes

    @property
    def trace(self) -> tuple[str, ...]:
        """Error-return trace attached via :meth:`traced`, innermost first."""
        return self._trace

    @property
    def is_ok(self) -> bool:
        """Always ``False`` for ``Err``."""
        return False

    @property
    def is_err(self) -> bool:
        """Always ``True`` for ``Err``."""
        return True

    @property
    def ok(self) -> None:
        """Always ``None`` for ``Err``."""
        return None

    @property
    def err(self) -> E_co:
        """The wrapped error value."""
        return self._error

    @property
    def danger_ok(self) -> Any:
        """Always raises ``UnwrapError``: ``Err`` carries no success value."""
        raise UnwrapError(self)

    @property
    def danger_err(self) -> E_co:
        """The wrapped error value."""
        return self._error

    def is_ok_and(self, pred: Callable[[T_co], bool]) -> bool:
        """Always ``False``: ``Err`` has no success value to test."""
        return False

    def is_err_and(self, pred: Callable[[E_co], bool]) -> bool:
        """``True`` when *pred* holds for the wrapped error."""
        return bool(pred(self._error))

    def unwrap(self, *, err: F | None = None, note: str | None = None) -> T_co:
        """Always raises ``UnwrapError``: ``Err`` carries no success value.

        With *err* given the raised error's ``.container`` is
        ``self.wrap_err(err)`` (optionally further ``.note(note)``-d);
        with only *note* given it is ``self.note(note)``.
        """
        if err is None and note is None:
            raise UnwrapError(self)
        container: "Result[T_co, Any]" = self.wrap_err(err) if err is not None else self
        if note is not None:
            container = container.note(note)
        raise UnwrapError(container)

    def unwrap_err(self) -> E_co:
        """Return the wrapped error."""
        return self._error

    def unwrap_or(self, default: U) -> T_co | U:
        """Return *default*; the wrapped error is discarded."""
        return default

    def unwrap_or_else(self, fn: Callable[[E_co], U]) -> T_co | U:
        """Return ``fn(error)``."""
        return fn(self._error)

    def expect(self, msg: str) -> T_co:
        """Always raises ``UnwrapError`` prefixed with *msg*: no success value here."""
        raise UnwrapError(self, msg)

    def expect_err(self, msg: str) -> E_co:
        """Return the wrapped error; *msg* is never used."""
        return self._error

    def inspect(self, fn: Callable[[T_co], None]) -> "Err[T_co, E_co]":
        """No-op: ``Err`` has no success value to inspect; return ``self``."""
        return self

    def inspect_err(self, fn: Callable[[E_co], None]) -> "Err[T_co, E_co]":
        """Call *fn* with the wrapped error for side effects; return ``self``."""
        fn(self._error)
        return self

    def fold(self, on_ok: Callable[[T_co], U], on_err: Callable[[E_co], U]) -> U:
        """Return ``on_err(error)``; *on_ok* is never called."""
        return on_err(self._error)

    def to_option(self) -> "Option[T_co]":
        """Convert to :class:`~typani.option.Nothing`; the error is discarded."""
        # Local import: avoids a module-level cycle with typani.option.
        from typani.option import Nothing

        return Nothing()

    def __eq__(self, other: object) -> bool:
        """Equal to another ``Err`` with an equal payload; notes are not compared."""
        if not isinstance(other, Err):
            return NotImplemented
        return bool(self._error == other._error)

    def __ne__(self, other: object) -> bool:
        """Inverse of :meth:`__eq__`."""
        result = self.__eq__(other)
        if result is NotImplemented:
            return result  # type: ignore[no-any-return]
        return not result

    def __hash__(self) -> int:
        """Hash derived from the variant marker and error payload (notes excluded)."""
        return hash((_ERR_MARKER, self._error))

    def __repr__(self) -> str:
        """``Err(<repr>)``, with notes/trace appended when present.

        Notes render as ``"; note: a; note: b"``; a non-empty trace renders
        as ``"; via inner <- outer"`` (innermost site first), after notes.
        """
        base = f"Err({self._error!r})"
        return self._render_meta(base)

    def __str__(self) -> str:
        """``Err(<str>)``, with notes/trace appended when present (see ``__repr__``)."""
        base = f"Err({self._error!s})"
        return self._render_meta(base)

    def _render_meta(self, base: str) -> str:
        """Append ``"; note: ..."`` and ``"; via a <- b"`` segments when present."""
        suffix = "".join(f"; note: {note}" for note in self._notes)
        if self._trace:
            suffix += "; via " + " <- ".join(self._trace)
        if not suffix:
            return base
        return base[:-1] + suffix + ")"

    def __reduce__(
        self,
    ) -> tuple[
        Callable[..., "Err[T_co, E_co]"],
        tuple[E_co, tuple[str, ...], tuple[str, ...]],
    ]:
        """Pickle support: rebuild via the module helper, keeping notes/trace."""
        return (_rebuild_err, (self._error, self._notes, self._trace))

    def __deepcopy__(self, memo: dict[int, object]) -> "Err[T_co, E_co]":
        """Return a new ``Err`` with a deep-copied error, preserving notes/trace."""
        return Err(_copy.deepcopy(self._error, memo))._with_meta(
            self._notes, self._trace
        )


if not TYPE_CHECKING:
    # T-0010: bind the public names to the native PyO3 classes when the
    # backend selection (typani._impl.native_active) picks native, so
    # everything that does `from typani.result import Ok` at runtime gets
    # the accelerated class. Type checkers never see this branch, so they
    # keep resolving against the pure-Python definitions above regardless
    # of which backend actually runs.
    from typani._impl import native_active as _native_active

    if _native_active():
        import typani_core as _typani_core

        Result = _typani_core.Result
        Ok = _typani_core.Ok
        Err = _typani_core.Err
        # _rebuild_err stays the pure-Python function above: the native
        # Err.__reduce__ calls it by name via `typani.result._rebuild_err`
        # (see crates/typani-core/src/result.rs), so both backends' Err
        # pickles reconstruct through this single entry point.
