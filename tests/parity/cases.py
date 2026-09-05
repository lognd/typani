"""Shared table of Result/Option expressions exercised for backend parity (T-0010).

Each entry is ``(name, thunk)`` where *thunk* takes no arguments and
returns a JSON-serializable value, or raises. `run_case.py` executes every
entry under whichever backend the process was started with (native or
pure, selected via `TYPANI_PURE`) and reports the outcome as one JSON
record per case; `tests/test_backend.py` runs this twice (native, pure)
and diffs the two reports.
"""

from __future__ import annotations

import pickle
from typing import Any, Callable

import typani
from typani.option import Nothing, Some
from typani.result import Err, Ok


def _repr_pair(x: object) -> dict[str, Any]:
    """Serialize an arbitrary result value as its repr/str/type-name triple."""
    return {"repr": repr(x), "str": str(x), "type": type(x).__name__}


def _case(fn: Callable[[], object]) -> Callable[[], dict[str, Any]]:
    """Wrap *fn* so exceptions are captured as data instead of propagating."""

    def wrapped() -> dict[str, Any]:
        try:
            value = fn()
        except Exception as exc:  # noqa: BLE001 -- parity harness captures everything
            return {"exc_type": type(exc).__name__, "exc_str": str(exc)}
        return _repr_pair(value)

    return wrapped


def _match_ok(r: Ok[int, object]) -> dict[str, int]:
    """Structural-match an ``Ok``, exercising `__match_args__` on both backends."""
    match r:
        case Ok(v):
            return {"v": v}
        case _:  # pragma: no cover -- unreachable for an Ok argument
            raise AssertionError("Ok did not match Ok(v)")


CASES: dict[str, Callable[[], dict[str, Any]]] = {
    "ok_ctor": _case(lambda: Ok(1)),
    "err_ctor": _case(lambda: Err("boom")),
    "some_ctor": _case(lambda: Some(1)),
    "nothing_ctor": _case(lambda: Nothing()),
    "nothing_singleton": _case(lambda: Nothing() is Nothing()),
    "ok_is_ok": _case(lambda: Ok(1).is_ok),
    "ok_is_err": _case(lambda: Ok(1).is_err),
    "err_is_ok": _case(lambda: Err(1).is_ok),
    "err_is_err": _case(lambda: Err(1).is_err),
    "ok_unwrap": _case(lambda: Ok(1).unwrap()),
    "err_unwrap": _case(lambda: Err(1).unwrap()),
    "ok_unwrap_err": _case(lambda: Ok(1).unwrap_err()),
    "err_unwrap_err": _case(lambda: Err(1).unwrap_err()),
    "ok_danger_ok": _case(lambda: Ok(1).danger_ok),
    "ok_danger_err": _case(lambda: Ok(1).danger_err),
    "err_danger_ok": _case(lambda: Err(1).danger_ok),
    "err_danger_err": _case(lambda: Err(1).danger_err),
    "ok_expect": _case(lambda: Ok(1).expect("msg")),
    "err_expect": _case(lambda: Err(1).expect("msg")),
    "ok_expect_err": _case(lambda: Ok(1).expect_err("msg")),
    "err_expect_err": _case(lambda: Err(1).expect_err("msg")),
    "ok_unwrap_or": _case(lambda: Ok(1).unwrap_or(9)),
    "err_unwrap_or": _case(lambda: Err(1).unwrap_or(9)),
    "ok_map": _case(lambda: Ok(1).map(lambda x: x + 1)),
    "err_map": _case(lambda: Err(1).map(lambda x: x + 1)),
    "ok_map_err": _case(lambda: Ok(1).map_err(str)),
    "err_map_err": _case(lambda: Err(1).map_err(str)),
    "ok_and_then": _case(lambda: Ok(1).and_then(lambda x: Ok(x + 1))),
    "err_and_then": _case(lambda: Err(1).and_then(lambda x: Ok(x + 1))),
    "ok_or_else": _case(lambda: Ok(1).or_else(lambda e: Err(str(e)))),
    "err_or_else": _case(lambda: Err(1).or_else(lambda e: Ok(str(e)))),
    "err_note": _case(lambda: Err("x").note("ctx")),
    "err_note_repr": _case(lambda: repr(Err("x").note("a").note("b"))),
    "ok_to_option": _case(lambda: Ok(1).to_option()),
    "err_to_option": _case(lambda: Err(1).to_option()),
    "ok_eq_ok": _case(lambda: Ok(1) == Ok(1)),
    "ok_eq_ok_false": _case(lambda: Ok(1) == Ok(2)),
    "ok_hash_stable": _case(lambda: hash(Ok(1)) == hash(Ok(1))),
    "ok_bool_raises": _case(lambda: bool(Ok(1))),
    "some_map": _case(lambda: Some(1).map(lambda x: x + 1)),
    "nothing_map": _case(lambda: Nothing().map(lambda x: x + 1)),
    "nothing_and_then": _case(lambda: Nothing().and_then(lambda x: Some(x))),
    "nothing_or_else": _case(lambda: Nothing().or_else(lambda: Some(9))),
    "some_unwrap": _case(lambda: Some(1).unwrap()),
    "nothing_unwrap": _case(lambda: Nothing().unwrap()),
    "some_filter_true": _case(lambda: Some(1).filter(lambda x: x > 0)),
    "some_filter_false": _case(lambda: Some(1).filter(lambda x: x < 0)),
    "some_ok_or": _case(lambda: Some(1).ok_or("e")),
    "nothing_ok_or": _case(lambda: Nothing().ok_or("e")),
    "match_ok": _case(lambda: _match_ok(Ok(1))),
    "propagate_unwrap": _case(lambda: typani.propagate(lambda: Err("x").unwrap())()),
    "pickle_ok": _case(lambda: pickle.loads(pickle.dumps(Ok(1)))),
    "pickle_err_notes": _case(lambda: pickle.loads(pickle.dumps(Err("x").note("a")))),
    "pickle_some": _case(lambda: pickle.loads(pickle.dumps(Some(1)))),
    "pickle_nothing": _case(lambda: pickle.loads(pickle.dumps(Nothing()))),
    "deepcopy_err": _case(lambda: __import__("copy").deepcopy(Err([1, 2]).note("n"))),
    "isinstance_result": _case(lambda: isinstance(Ok(1), typani.Result)),
    "isinstance_option": _case(lambda: isinstance(Some(1), typani.Option)),
}
