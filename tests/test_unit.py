import pytest

from typani.unit import Unit, UnitMeta


def test_unit_has_no_slots() -> None:
    u = Unit()
    assert u.__slots__ == ()


def test_unit_subclass_has_no_slots() -> None:
    class Sub(Unit): ...

    s = Sub()
    assert s.__slots__ == ()


def test_unit_subclass_cannot_set_attributes() -> None:
    class Sub(Unit): ...

    s = Sub()
    with pytest.raises(AttributeError):
        s.x = 1  # type: ignore[attr-defined]


def test_unit_meta_forces_slots_on_subclass() -> None:
    class Custom(metaclass=UnitMeta): ...

    # __slots__ is set by UnitMeta at class creation time; verify via __dict__
    # and by confirming instances cannot carry arbitrary attributes.
    assert Custom.__dict__["__slots__"] == ()
    with pytest.raises(AttributeError):
        Custom().x = 1  # type: ignore[attr-defined]


def test_unit_instances_are_independent() -> None:
    a = Unit()
    b = Unit()
    assert a is not b
