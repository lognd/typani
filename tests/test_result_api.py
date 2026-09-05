"""Tests for the 0.1 Result API: variants as classes, notes, catch, pickling."""

from __future__ import annotations

import copy
import pickle
import subprocess
import sys

import pytest

from typani._exceptions import UnwrapError
from typani.result import Err, Ok, Result

# --- construction / abstractness -------------------------------------------


# frob:tests src/typani/result.py::Result
def test_result_direct_construction_raises() -> None:
    with pytest.raises(TypeError, match="abstract"):
        Result()  # type: ignore[call-overload]


# --- match statements / isinstance narrowing --------------------------------


# frob:tests src/typani/result.py::Ok
def test_match_ok() -> None:
    r: Result[int, str] = Ok(5)
    match r:
        case Ok(v):
            assert v == 5
        case Err(_):
            pytest.fail("matched Err")


# frob:tests src/typani/result.py::Err
def test_match_err() -> None:
    r: Result[int, str] = Err("bad")
    match r:
        case Ok(_):
            pytest.fail("matched Ok")
        case Err(e):
            assert e == "bad"


def test_isinstance_narrowing() -> None:
    r: Result[int, str] = Ok(1)
    assert isinstance(r, Ok)
    assert isinstance(r, Result)
    assert not isinstance(r, Err)


# --- equality / hashing ------------------------------------------------------


# frob:tests src/typani/result.py::Ok.__eq__
def test_ok_equality() -> None:
    assert Ok(1) == Ok(1)
    assert Ok(1) != Ok(2)
    assert Ok(1) != Err(1)
    assert Ok(1).__eq__(object()) is NotImplemented


# frob:tests src/typani/result.py::Err.__eq__
def test_err_equality_ignores_notes() -> None:
    plain = Err("x")
    noted = Err("x").note("context")
    assert plain == noted


def test_hashing_dict_and_set() -> None:
    d = {Ok(1): "a", Err("x"): "b"}
    assert d[Ok(1)] == "a"
    assert d[Err("x")] == "b"
    s = {Ok(1), Ok(1), Err("x")}
    assert len(s) == 2


# --- iteration / bool ---------------------------------------------------------


def test_iter_ok_yields_value() -> None:
    assert list(Ok(3)) == [3]


def test_iter_err_yields_nothing() -> None:
    assert list(Err("x")) == []


def test_bool_raises() -> None:
    with pytest.raises(TypeError, match="truth value"):
        bool(Ok(1))
    with pytest.raises(TypeError):
        bool(Err("x"))


# --- repr / str, with and without notes --------------------------------------


def test_repr_str_plain() -> None:
    assert repr(Ok(1)) == "Ok(1)"
    assert repr(Err("x")) == "Err('x')"
    assert str(Ok(1)) == "Ok(1)"
    assert str(Err("x")) == "Err(x)"


def test_repr_str_with_notes() -> None:
    e = Err("x").note("a").note("b")
    assert repr(e) == "Err('x'; note: a; note: b)"
    assert str(e) == "Err(x; note: a; note: b)"


# --- notes ---------------------------------------------------------------------


# frob:tests src/typani/result.py::Result.note
def test_notes_accumulate() -> None:
    e = Err("x").note("first").note("second")
    assert e.notes == ("first", "second")


def test_ok_note_is_noop() -> None:
    o = Ok(1)
    assert o.note("ignored") is o
    assert o.notes == ()


def test_notes_survive_map_err() -> None:
    e = Err("x").note("ctx").map_err(str.upper)
    assert e.err == "X"
    assert e.notes == ("ctx",)


# --- unwrap / expect variants ---------------------------------------------------


def test_unwrap_ok_and_err() -> None:
    assert Ok(1).unwrap() == 1
    with pytest.raises(UnwrapError):
        Err("x").unwrap()


def test_unwrap_err_variants() -> None:
    assert Err("x").unwrap_err() == "x"
    with pytest.raises(UnwrapError):
        Ok(1).unwrap_err()


def test_unwrap_or() -> None:
    assert Ok(1).unwrap_or(9) == 1
    assert Err("x").unwrap_or(9) == 9


def test_unwrap_or_else() -> None:
    assert Ok(1).unwrap_or_else(lambda e: 9) == 1
    assert Err("x").unwrap_or_else(lambda e: len(e)) == 1


def test_expect_and_expect_err() -> None:
    assert Ok(1).expect("boom") == 1
    with pytest.raises(UnwrapError, match="boom"):
        Err("x").expect("boom")
    assert Err("x").expect_err("boom") == "x"
    with pytest.raises(UnwrapError, match="boom"):
        Ok(1).expect_err("boom")


def test_danger_ok_and_danger_err() -> None:
    assert Ok(1).danger_ok == 1
    assert Err("x").danger_err == "x"
    with pytest.raises(UnwrapError):
        _ = Err("x").danger_ok
    with pytest.raises(UnwrapError):
        _ = Ok(1).danger_err


def test_python_o_safety() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-O",
            "-c",
            "from typani import Err, UnwrapError\n"
            "try:\n"
            "    Err(1).danger_ok\n"
            "    raise SystemExit(1)\n"
            "except UnwrapError:\n"
            "    raise SystemExit(0)\n",
        ],
        cwd="/home/logan/projects/typani",
        env={"PYTHONPATH": "src"},
    )
    assert proc.returncode == 0


# --- UnwrapError attributes -------------------------------------------------


def test_unwrap_error_container_and_message() -> None:
    err = Err("boom")
    try:
        err.unwrap()
    except UnwrapError as exc:
        assert exc.container is err
        assert "Err" in str(exc)


# --- is_ok_and / is_err_and / fold / to_option --------------------------------


def test_is_ok_and_is_err_and() -> None:
    assert Ok(4).is_ok_and(lambda x: x > 0)
    assert not Ok(-1).is_ok_and(lambda x: x > 0)
    assert Err("x").is_err_and(lambda e: e == "x")
    assert not Err("x").is_err_and(lambda e: e == "y")


def test_fold() -> None:
    assert Ok(1).fold(lambda v: v + 1, lambda e: 0) == 2
    assert Err("x").fold(lambda v: v + 1, lambda e: 0) == 0


def test_to_option() -> None:
    from typani.option import Nothing, Some

    assert Ok(1).to_option() == Some(1)
    assert Err("x").to_option() == Nothing()


def test_inspect_and_inspect_err() -> None:
    seen: list[int] = []
    Ok(1).inspect(seen.append)
    Err("x").inspect(seen.append)
    assert seen == [1]
    seen_err: list[str] = []
    Err("x").inspect_err(seen_err.append)
    Ok(1).inspect_err(seen_err.append)
    assert seen_err == ["x"]


# --- swap_* -------------------------------------------------------------------


def test_swap_ok_and_swap_err_raise() -> None:
    Ok(1).swap_err(int)
    Err("x").swap_ok(str)
    with pytest.raises(UnwrapError):
        Err("x").swap_err(int)
    with pytest.raises(UnwrapError):
        Ok(1).swap_ok(str)


# --- catch ----------------------------------------------------------------------


# frob:tests src/typani/result.py::Result.catch
def test_catch_ok() -> None:
    r = Result.catch(lambda: 1 / 1, ZeroDivisionError, on_error=lambda e: str(e))
    assert r == Ok(1.0)


def test_catch_err() -> None:
    r = Result.catch(lambda: 1 / 0, ZeroDivisionError, on_error=lambda e: str(e))
    assert r.is_err


def test_catch_default_exception() -> None:
    r = Result.catch(lambda: 1 / 0, on_error=lambda e: type(e).__name__)
    assert r.err == "ZeroDivisionError"


# --- pickle / copy / deepcopy ---------------------------------------------------


def test_pickle_roundtrip_ok() -> None:
    o = Ok(1)
    assert pickle.loads(pickle.dumps(o)) == o


def test_pickle_roundtrip_err_preserves_notes() -> None:
    e = Err("x").note("ctx")
    restored = pickle.loads(pickle.dumps(e))
    assert restored == e
    assert restored.notes == ("ctx",)


def test_copy_returns_self() -> None:
    o = Ok(1)
    assert copy.copy(o) is o


def test_deepcopy_new_payload() -> None:
    inner = [1, 2]
    o = Ok(inner)
    dup = copy.deepcopy(o)
    assert dup == o
    assert dup.danger_ok is not inner

    e = Err(["x"]).note("ctx")
    dup_e = copy.deepcopy(e)
    assert dup_e == e
    assert dup_e.notes == ("ctx",)
