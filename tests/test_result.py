import pytest

from typani.result import Err, Ok, Result


def test_ok_is_ok() -> None:
    r: Result[int, str] = Ok(42)
    assert r.is_ok
    assert not r.is_err
    assert r.ok == 42
    assert r.err is None


def test_err_is_err() -> None:
    r: Result[int, str] = Err("oops")
    assert r.is_err
    assert not r.is_ok
    assert r.err == "oops"
    assert r.ok is None


def test_neither_ok_nor_err_raises() -> None:
    with pytest.raises(TypeError, match="neither"):
        Result()  # type: ignore[call-overload]


def test_both_ok_and_err_raises() -> None:
    with pytest.raises(TypeError, match="both"):
        Result(ok=1, err="x")  # type: ignore[call-overload]


def test_map_on_ok() -> None:
    r: Result[int, str] = Ok(5)
    assert r.map(lambda x: x * 2).ok == 10


def test_map_on_err_is_noop() -> None:
    r: Result[int, str] = Err("bad")
    mapped = r.map(lambda x: x * 2)
    assert mapped.is_err
    assert mapped.err == "bad"


def test_map_err_on_err() -> None:
    r: Result[int, str] = Err("bad")
    assert r.map_err(lambda s: s.upper()).err == "BAD"


def test_map_err_on_ok_is_noop() -> None:
    r: Result[int, str] = Ok(1)
    assert r.map_err(lambda s: s.upper()).is_ok


def test_and_then_chains_ok() -> None:
    r: Result[int, str] = Ok(3)
    result = r.and_then(lambda x: Ok(x + 1))
    assert result.ok == 4


def test_and_then_propagates_first_err() -> None:
    r: Result[int, str] = Err("first")
    result = r.and_then(lambda x: Ok(x + 1))
    assert result.err == "first"


def test_and_then_propagates_inner_err() -> None:
    r: Result[int, str] = Ok(1)
    result = r.and_then(lambda _: Err("inner"))
    assert result.err == "inner"


def test_or_else_on_err() -> None:
    r: Result[int, str] = Err("bad")
    result = r.or_else(lambda e: Ok(0))
    assert result.ok == 0


def test_or_else_on_ok_is_noop() -> None:
    r: Result[int, str] = Ok(99)
    result = r.or_else(lambda e: Ok(0))
    assert result.ok == 99


def test_inspect_called_on_ok() -> None:
    seen: list[int] = []
    Ok(7).inspect(seen.append)
    assert seen == [7]


def test_inspect_not_called_on_err() -> None:
    seen: list[int] = []
    Err("x").inspect(seen.append)
    assert seen == []


def test_danger_ok_asserts_on_err() -> None:
    with pytest.raises(AssertionError):
        _ = Err("x").danger_ok  # type: ignore[union-attr]


def test_danger_err_asserts_on_ok() -> None:
    with pytest.raises(AssertionError):
        _ = Ok(1).danger_err  # type: ignore[union-attr]


def test_swap_err_on_ok() -> None:
    r: Result[int, str] = Ok(1)
    swapped: Result[int, int] = r.swap_err(int)
    assert swapped.is_ok


def test_swap_ok_on_err() -> None:
    r: Result[int, str] = Err("e")
    swapped: Result[str, str] = r.swap_ok(str)
    assert swapped.is_err


def test_repr_ok() -> None:
    assert repr(Ok(42)) == "Ok(42)"


def test_repr_err() -> None:
    assert repr(Err("bad")) == "Err('bad')"


def test_str_ok() -> None:
    assert str(Ok(42)) == "Ok(42)"


def test_str_err() -> None:
    assert str(Err("bad")) == "Err(bad)"
