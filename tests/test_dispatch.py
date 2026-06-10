import pytest

from typani.dispatch import dispatch


def test_dispatches_to_matching_type() -> None:
    result = dispatch(42, {int: lambda x: x * 2, str: lambda s: s.upper()})
    assert result == 84


def test_dispatches_to_str() -> None:
    result = dispatch("hello", {int: lambda x: x * 2, str: lambda s: s.upper()})
    assert result == "HELLO"


def test_subclass_matches_parent_key() -> None:
    class MyInt(int): ...

    result = dispatch(MyInt(5), {int: lambda x: x + 1})
    assert result == 6


def test_first_match_wins() -> None:
    result = dispatch(True, {bool: lambda _: "bool", int: lambda _: "int"})
    assert result == "bool"


def test_raises_when_no_match_and_no_default() -> None:
    with pytest.raises(TypeError, match="no handler"):
        dispatch(3.14, {int: lambda x: x, str: lambda s: s})


def test_returns_default_when_no_match() -> None:
    result = dispatch(3.14, {int: lambda x: x}, default="fallback")
    assert result == "fallback"


def test_default_none_is_valid() -> None:
    result: str | None = dispatch(3.14, {int: lambda x: str(x)}, default=None)
    assert result is None


def test_empty_cases_uses_default() -> None:
    assert dispatch(1, {}, default=99) == 99


def test_empty_cases_raises_without_default() -> None:
    with pytest.raises(TypeError):
        dispatch(1, {})
