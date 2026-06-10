from __future__ import annotations


class UnitMeta(type):
    """Metaclass that forces ``__slots__ = ()`` on every class it creates.

    This prevents subclasses from accidentally carrying instance state by
    ensuring no ``__dict__`` is allocated and no attributes can be set.
    """

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        # Force zero slots.
        namespace["__slots__"] = ()
        return super().__new__(mcls, name, bases, namespace, **kwargs)


class Unit(metaclass=UnitMeta):
    """Zero-slot base class for marker and sentinel types.

    Any subclass is guaranteed to carry no instance attributes.  Useful
    wherever you need a type-safe, zero-cost presence marker -- the Python
    equivalent of Rust's ``()`` or Haskell's ``Unit``.

    Example::

        class MyMarker(Unit): ...

        m = MyMarker()  # valid
        m.x = 1         # AttributeError
    """

    # Declared here so type checkers can resolve the attribute.
    # UnitMeta.__new__ forces this to () on every subclass as well.
    __slots__ = ()
