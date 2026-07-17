import pytest

from typani.option import Nothing, Option, Some


# frob:tests src/typani/option.py::Some
# frob:tests src/typani/option.py::Option
def test_some_is_some() -> None:
    o: Option[int] = Some(5)
    assert o.is_some
    assert not o.is_nothing
    assert o.some == 5


# frob:tests src/typani/option.py::Nothing
# frob:tests src/typani/option.py::Option
def test_nothing_is_nothing() -> None:
    o: Option[int] = Nothing()
    assert o.is_nothing
    assert not o.is_some
    assert o.some is None


def test_map_on_some() -> None:
    assert Some(3).map(lambda x: x * 2).some == 6


def test_map_on_nothing_is_noop() -> None:
    result: Option[int] = Nothing()
    mapped = result.map(lambda x: x * 2)
    assert mapped.is_nothing


def test_and_then_chains_some() -> None:
    result = Some(4).and_then(lambda x: Some(x + 1))
    assert result.some == 5


def test_and_then_propagates_nothing() -> None:
    result: Option[int] = Nothing()
    assert result.and_then(lambda x: Some(x + 1)).is_nothing


def test_and_then_inner_nothing() -> None:
    result = Some(1).and_then(lambda _: Nothing())
    assert result.is_nothing


def test_or_else_on_nothing() -> None:
    result: Option[int] = Nothing()
    assert result.or_else(lambda: Some(99)).some == 99


def test_or_else_on_some_is_noop() -> None:
    result: Option[int] = Some(7)
    assert result.or_else(lambda: Some(0)).some == 7


def test_inspect_called_on_some() -> None:
    seen: list[int] = []
    Some(10).inspect(seen.append)
    assert seen == [10]


def test_inspect_not_called_on_nothing() -> None:
    seen: list[int] = []
    nothing: Option[int] = Nothing()
    nothing.inspect(seen.append)
    assert seen == []


def test_unwrap_or_some() -> None:
    assert Some(3).unwrap_or(0) == 3


def test_unwrap_or_nothing() -> None:
    result: Option[int] = Nothing()
    assert result.unwrap_or(0) == 0


def test_danger_some_asserts_on_nothing() -> None:
    nothing: Option[int] = Nothing()
    with pytest.raises(AssertionError):
        _ = nothing.danger_some


def test_repr_some() -> None:
    assert repr(Some(42)) == "Some(42)"


def test_repr_nothing() -> None:
    assert repr(Nothing()) == "Nothing"


def test_str_some() -> None:
    assert str(Some("hi")) == "Some(hi)"


def test_str_nothing() -> None:
    assert str(Nothing()) == "Nothing"
