"""Tests for the 0.1 Result API: variants as classes, notes, catch, pickling."""

from __future__ import annotations

import copy
import os
import pickle
import subprocess
import sys
from pathlib import Path

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


# frob:tests src/typani/result.py::Err
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
        cwd=Path(__file__).resolve().parents[1],
        # Extend, never replace, the environment: a bare env cannot start
        # Python on Windows (SYSTEMROOT is required).
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


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


# --- wrap_err (T-0028) -------------------------------------------------------


# frob:tests src/typani/result.py::Result.wrap_err
def test_wrap_err_ok_passthrough() -> None:
    o = Ok(1)
    assert o.wrap_err("NEW") is o


# frob:tests src/typani/result.py::Result.wrap_err
def test_wrap_err_err_mapping() -> None:
    w = Err("bad").wrap_err("NEW")
    assert w == Err("NEW")
    assert w.notes == ("caused by 'bad'",)


def test_wrap_err_preserves_existing_notes_before_cause() -> None:
    w = Err("bad").note("ctx").wrap_err("NEW")
    assert w.notes == ("ctx", "caused by 'bad'")


def test_wrap_err_repr_shape() -> None:
    w = Err("bad").wrap_err("NEW")
    assert repr(w) == "Err('NEW'; note: caused by 'bad')"


def test_wrap_err_under_propagate() -> None:
    from typani import propagate

    @propagate
    def fn() -> "Result[int, str]":
        Err("bad").wrap_err("NEW").unwrap()
        raise AssertionError("unreachable")

    result = fn()
    assert result == Err("NEW")
    assert result.notes == ("caused by 'bad'",)


def test_wrap_err_pickle_round_trip_keeps_note() -> None:
    w = Err("bad").wrap_err("NEW")
    restored = pickle.loads(pickle.dumps(w))
    assert restored == w
    assert restored.notes == w.notes


# --- unwrap(err=, note=) keyword sugar (T-0028) -------------------------------


# frob:tests src/typani/result.py::Err.unwrap
def test_unwrap_ok_ignores_keywords() -> None:
    assert Ok(1).unwrap(err="NEW") == 1
    assert Ok(1).unwrap(note="n") == 1


# frob:tests src/typani/result.py::Err.unwrap
def test_unwrap_err_with_err_mapped_container() -> None:
    with pytest.raises(UnwrapError) as excinfo:
        Err("bad").unwrap(err="NEW")
    container = excinfo.value.container
    assert isinstance(container, Err)
    assert container == Err("NEW")
    assert container.notes == ("caused by 'bad'",)


def test_unwrap_err_with_err_and_note() -> None:
    with pytest.raises(UnwrapError) as excinfo:
        Err("bad").unwrap(err="NEW", note="ctx")
    container = excinfo.value.container
    assert isinstance(container, Err)
    assert container == Err("NEW")
    assert container.notes == ("caused by 'bad'", "ctx")


def test_unwrap_err_equivalence_to_wrap_err_note_unwrap() -> None:
    """`r.unwrap(err=E, note=N) == r.wrap_err(E).note(N).unwrap()` (raises equally)."""
    r = Err("bad")
    with pytest.raises(UnwrapError) as via_kwargs:
        r.unwrap(err="NEW", note="ctx")
    with pytest.raises(UnwrapError) as via_chain:
        r.wrap_err("NEW").note("ctx").unwrap()
    kwargs_container = via_kwargs.value.container
    chain_container = via_chain.value.container
    assert isinstance(kwargs_container, Err)
    assert isinstance(chain_container, Err)
    assert kwargs_container == chain_container
    assert kwargs_container.notes == chain_container.notes


def test_unwrap_note_only_appends_to_existing_err() -> None:
    with pytest.raises(UnwrapError) as excinfo:
        Err("bad").unwrap(note="ctx")
    container = excinfo.value.container
    assert isinstance(container, Err)
    assert container == Err("bad")
    assert container.notes == ("ctx",)


def test_unwrap_bare_unaffected() -> None:
    with pytest.raises(UnwrapError) as excinfo:
        Err("bad").unwrap()
    container = excinfo.value.container
    assert isinstance(container, Err)
    assert container == Err("bad")
    assert container.notes == ()


# --- error-return trace (T-0028) ----------------------------------------------


# frob:tests src/typani/result.py::Err.traced
def test_traced_ok_is_noop() -> None:
    o = Ok(1)
    assert o.traced("site") is o


def test_traced_appends_innermost_first() -> None:
    e = Err("bad").traced("a").traced("b").traced("c")
    assert e.trace == ("a", "b", "c")


def test_traced_repr_shape() -> None:
    e = Err("bad").traced("inner").traced("outer")
    assert repr(e) == "Err('bad'; via inner <- outer)"


def test_traced_with_notes_repr_order() -> None:
    e = Err("bad").note("n1").note("n2").traced("inner").traced("outer")
    assert repr(e) == "Err('bad'; note: n1; note: n2; via inner <- outer)"


def test_trace_survives_note_wrap_err_map_err() -> None:
    e = Err("bad").traced("site1")
    assert e.note("n").trace == ("site1",)
    assert e.wrap_err("NEW").trace == ("site1",)
    assert e.map_err(str.upper).trace == ("site1",)


def test_trace_survives_unwrap_err_kwarg() -> None:
    e = Err("bad").traced("site1")
    with pytest.raises(UnwrapError) as excinfo:
        e.unwrap(err="NEW")
    container = excinfo.value.container
    assert isinstance(container, Err)
    assert container.trace == ("site1",)


def test_trace_three_hop_propagate_order() -> None:
    from typani import propagate

    @propagate
    def inner() -> "Result[int, str]":
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    @propagate
    def middle() -> "Result[int, str]":
        inner().unwrap()
        raise AssertionError("unreachable")

    @propagate
    def outer() -> "Result[int, str]":
        middle().unwrap()
        raise AssertionError("unreachable")

    result = outer()
    assert result == Err("bad")
    assert len(result.trace) == 3
    assert result.trace[0].startswith(
        "test_trace_three_hop_propagate_order.<locals>.inner:"
    )
    assert result.trace[1].startswith(
        "test_trace_three_hop_propagate_order.<locals>.middle:"
    )
    assert result.trace[2].startswith(
        "test_trace_three_hop_propagate_order.<locals>.outer:"
    )


def test_trace_pickle_round_trip() -> None:
    e = Err("bad").traced("a").traced("b")
    restored = pickle.loads(pickle.dumps(e))
    assert restored == e
    assert restored.trace == e.trace


def test_trace_ignored_by_equality_and_hash() -> None:
    plain = Err("bad")
    traced = Err("bad").traced("site")
    assert plain == traced
    assert hash(plain) == hash(traced)


def test_trace_backward_compatible_pickle_two_arg_rebuild() -> None:
    """Older pickles used the 2-arg `_rebuild_err(error, notes)` form."""
    from typani.result import _rebuild_err

    rebuilt = _rebuild_err("bad", ("ctx",))
    assert rebuilt == Err("bad")
    assert rebuilt.notes == ("ctx",)
    assert rebuilt.trace == ()
