import pytest

from typani.unreachable import Unreachable


def test_unreachable_raises_on_instantiation() -> None:
    with pytest.raises(TypeError, match="UNREACHABLE"):
        Unreachable()


def test_unreachable_error_includes_location() -> None:
    with pytest.raises(TypeError) as exc_info:
        Unreachable()
    msg = str(exc_info.value)
    assert "test_unreachable.py" in msg
    assert "test_unreachable_error_includes_location" in msg


def test_unreachable_is_subclass_of_unit() -> None:
    from typani.unit import Unit

    assert issubclass(Unreachable, Unit)
