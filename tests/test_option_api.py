"""Tests for the 0.1 Option API: variants as classes, singleton Nothing, pickling."""

from __future__ import annotations

import copy
import pickle

import pytest

from typani._exceptions import UnwrapError
from typani.option import Nothing, Option, Some
from typani.result import Err, Ok

# --- construction / abstractness -------------------------------------------


def test_option_direct_construction_raises() -> None:
    with pytest.raises(TypeError, match="abstract"):
        Option()  # type: ignore[call-overload]


# frob:tests src/typani/option.py::Nothing
def test_nothing_is_singleton() -> None:
    assert Nothing() is Nothing()


# --- match statements / isinstance narrowing --------------------------------


# frob:tests src/typani/option.py::Some
def test_match_some() -> None:
    o: Option[int] = Some(5)
    match o:
        case Some(v):
            assert v == 5
        case Nothing():
            pytest.fail("matched Nothing")


# frob:tests src/typani/option.py::Nothing
def test_match_nothing() -> None:
    o: Option[int] = Nothing()
    match o:
        case Some(_):
            pytest.fail("matched Some")
        case Nothing():
            pass


def test_isinstance_narrowing() -> None:
    o: Option[int] = Some(1)
    assert isinstance(o, Some)
    assert isinstance(o, Option)
    assert not isinstance(o, Nothing)


# --- equality / hashing ------------------------------------------------------


def test_some_equality() -> None:
    assert Some(1) == Some(1)
    assert Some(1) != Some(2)
    assert Some(1) != Nothing()
    assert Some(1).__eq__(object()) is NotImplemented


def test_nothing_equality() -> None:
    assert Nothing() == Nothing()


def test_hashing_dict_and_set() -> None:
    d = {Some(1): "a", Nothing(): "b"}
    assert d[Some(1)] == "a"
    assert d[Nothing()] == "b"
    s = {Some(1), Some(1), Nothing()}
    assert len(s) == 2


# --- iteration / bool -----------------------------------------------------------


def test_iter_some_yields_value() -> None:
    assert list(Some(3)) == [3]


def test_iter_nothing_yields_nothing() -> None:
    assert list(Nothing()) == []


def test_bool_raises() -> None:
    with pytest.raises(TypeError, match="truth value"):
        bool(Some(1))
    with pytest.raises(TypeError):
        bool(Nothing())


# --- repr / str ---------------------------------------------------------------


def test_repr_str() -> None:
    assert repr(Some(1)) == "Some(1)"
    assert repr(Nothing()) == "Nothing"
    assert str(Some("hi")) == "Some(hi)"
    assert str(Nothing()) == "Nothing"


# --- unwrap / expect -------------------------------------------------------------


def test_unwrap() -> None:
    assert Some(1).unwrap() == 1
    with pytest.raises(UnwrapError):
        Nothing().unwrap()


def test_unwrap_or() -> None:
    assert Some(1).unwrap_or(9) == 1
    assert Nothing().unwrap_or(9) == 9


def test_unwrap_or_else() -> None:
    assert Some(1).unwrap_or_else(lambda: 9) == 1
    assert Nothing().unwrap_or_else(lambda: 9) == 9


def test_expect() -> None:
    assert Some(1).expect("boom") == 1
    with pytest.raises(UnwrapError, match="boom"):
        Nothing().expect("boom")


def test_danger_some() -> None:
    assert Some(1).danger_some == 1
    with pytest.raises(UnwrapError):
        _ = Nothing().danger_some


# --- UnwrapError attributes -----------------------------------------------------


def test_unwrap_error_container() -> None:
    n = Nothing()
    try:
        n.unwrap()
    except UnwrapError as exc:
        assert exc.container is n
        assert "Nothing" in str(exc)


# --- map / and_then / or_else / inspect / filter --------------------------------


def test_map_and_and_then() -> None:
    assert Some(3).map(lambda x: x * 2) == Some(6)
    assert Nothing().map(lambda x: x * 2) == Nothing()
    assert Some(4).and_then(lambda x: Some(x + 1)) == Some(5)
    assert Nothing().and_then(lambda x: Some(x + 1)) == Nothing()


def test_or_else() -> None:
    assert Nothing().or_else(lambda: Some(9)) == Some(9)
    assert Some(1).or_else(lambda: Some(9)) == Some(1)


def test_inspect() -> None:
    seen: list[int] = []
    Some(1).inspect(seen.append)
    Nothing().inspect(seen.append)
    assert seen == [1]


# frob:tests src/typani/option.py::Option.filter
def test_filter() -> None:
    assert Some(4).filter(lambda x: x % 2 == 0) == Some(4)
    assert Some(3).filter(lambda x: x % 2 == 0) == Nothing()
    assert Nothing().filter(lambda x: True) == Nothing()


# --- ok_or / ok_or_else / from_optional / to Result interop ---------------------


# frob:tests src/typani/option.py::Option.ok_or
def test_ok_or() -> None:
    assert Some(1).ok_or("no value") == Ok(1)
    assert Nothing().ok_or("no value") == Err("no value")


def test_ok_or_else() -> None:
    assert Some(1).ok_or_else(lambda: "no value") == Ok(1)
    assert Nothing().ok_or_else(lambda: "no value") == Err("no value")


# frob:tests src/typani/option.py::Option.from_optional
def test_from_optional() -> None:
    assert Option.from_optional(5) == Some(5)
    assert Option.from_optional(None) == Nothing()


# --- pickle / copy / deepcopy ---------------------------------------------------


def test_pickle_roundtrip_some() -> None:
    o = Some(1)
    assert pickle.loads(pickle.dumps(o)) == o


def test_pickle_roundtrip_nothing() -> None:
    n = Nothing()
    assert pickle.loads(pickle.dumps(n)) == n


def test_copy_returns_self() -> None:
    o = Some(1)
    assert copy.copy(o) is o
    n = Nothing()
    assert copy.copy(n) is n


def test_deepcopy() -> None:
    inner = [1, 2]
    o = Some(inner)
    dup = copy.deepcopy(o)
    assert dup == o
    assert dup.danger_some is not inner

    n = Nothing()
    assert copy.deepcopy(n) is n
