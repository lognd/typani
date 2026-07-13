from __future__ import annotations

from typing import Any, Callable, TypeVar

from typani.dispatch import dispatch

R = TypeVar("R")

_MISSING = object()


class _SumMeta(type):
    """Metaclass that makes ``Sum`` subscriptable at the class level.

    ``Sum[A, B, C]`` returns a new subclass of :class:`Sum` whose
    ``_variants`` tuple is ``(A, B, C)``.
    """

    def __getitem__(cls, args: Any) -> type[Sum]:
        """Create a concrete sum type from the subscripted variant types."""
        variants: tuple[type, ...] = args if isinstance(args, tuple) else (args,)
        name = "Sum[{}]".format(
            ", ".join(getattr(t, "__name__", repr(t)) for t in variants)
        )
        return _SumMeta(name, (cls,), {"_variants": variants})  # type: ignore[return-value]


class Sum(metaclass=_SumMeta):
    """Declared sum type (tagged union) with exhaustive dispatch.

    Define a sum type by subscripting with its variant types::

        from typani.sum import Sum

        Shape = Sum[Circle, Square, Triangle]

    Then dispatch with :meth:`match`, which requires a handler for every
    declared variant::

        area = Shape.match(shape, {
            Circle:   lambda c: math.pi * c.radius ** 2,
            Square:   lambda s: s.side ** 2,
            Triangle: lambda t: 0.5 * t.base * t.height,
        })

    Omitting a variant raises ``TypeError`` (exhaustiveness check).  To allow
    partial matching, pass a *default*::

        label = Shape.match(shape, {Circle: lambda c: "round"}, default="other")

    Check membership with :meth:`check`::

        Shape.check(Circle())   # True
        Shape.check("hello")    # False

    Unlike bare :func:`dispatch`, ``Sum.match`` documents the closed set of
    types upfront and enforces coverage at call time.
    """

    _variants: tuple[type, ...] = ()

    @classmethod
    def match(
        cls,
        value: object,
        cases: dict[type[Any], Callable[[Any], R]],
        *,
        default: R | object = _MISSING,
    ) -> R:
        """Dispatch *value* to the matching handler, enforcing exhaustiveness.

        Iterates *cases* in insertion order (same as :func:`dispatch`).

        Raises ``TypeError`` if any variant declared in this sum type is absent
        from *cases* and no *default* is provided.
        """
        if default is _MISSING and cls._variants:
            uncovered = [v for v in cls._variants if v not in cases]
            if uncovered:
                missing = ", ".join(getattr(v, "__name__", repr(v)) for v in uncovered)
                raise TypeError(
                    f"Non-exhaustive match on {cls.__name__}: "
                    f"missing handlers for {missing}"
                )
        return dispatch(value, cases, default=default)

    @classmethod
    def check(cls, value: object) -> bool:
        """Return ``True`` if *value* is an instance of any declared variant."""
        return bool(cls._variants) and isinstance(value, cls._variants)
