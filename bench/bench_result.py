"""Micro-benchmarks for Result/Option (T-0010): compare native vs pure backends.

Run twice to compare backends::

    uv run python bench/bench_result.py            # active backend (native if any)
    TYPANI_PURE=1 uv run python bench/bench_result.py   # pure-Python backend

Prints a table of per-call nanosecond costs for the operations named in
docs/native.md's benchmark table. Uses stdlib `timeit`; no test framework
involved since this is a reporting script, not a correctness check.
"""

from __future__ import annotations

import logging
import timeit

import typani
from typani.option import Nothing, Some
from typani.result import Err, Ok

_log = logging.getLogger(__name__)

_REPEAT = 200_000


def _bench(label: str, stmt: object, *, number: int = _REPEAT) -> None:
    """Time *stmt* (a zero-arg callable) `number` times and print ns/call."""
    seconds = timeit.timeit(stmt, number=number)
    ns_per_call = (seconds / number) * 1e9
    print(f"{label:<24} {ns_per_call:8.1f} ns/call")


def main() -> None:
    """Run the fixed benchmark table and print results for the active backend."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _log.info("backend: %s", typani.backend_name())
    print(f"backend: {typani.backend_name()}")

    r = Ok(1)
    e = Err("boom")

    _bench("Ok(1)", lambda: Ok(1))
    _bench("Some(1)", lambda: Some(1))
    _bench("Nothing()", lambda: Nothing())
    _bench("r.unwrap()", r.unwrap)
    _bench(
        "is_err+danger_ok",
        lambda: (r.is_err, r.danger_ok if not r.is_err else None),
    )
    _bench(
        "map+and_then",
        lambda: Ok(1).map(lambda x: x + 1).and_then(lambda x: Ok(x * 2)),
    )
    _bench("Err(e).note('x')", lambda: Err("boom").note("x"))

    import pickle

    _bench("pickle roundtrip", lambda: pickle.loads(pickle.dumps(e)), number=20_000)


if __name__ == "__main__":
    main()
