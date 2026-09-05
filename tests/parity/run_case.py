"""Run every parity case (tests/parity/cases.py) and print one JSON record each.

Invoked as a subprocess by tests/test_backend.py, once with ``TYPANI_PURE=1``
set and once unset, so the two runs exercise the pure and (if available)
native backends independently of this process's own import state.
"""

from __future__ import annotations

import json
import sys

from cases import CASES


def main() -> None:
    """Execute every case in `CASES` and emit ``{name: result}`` as JSON to stdout."""
    report = {name: case() for name, case in CASES.items()}
    json.dump(report, sys.stdout)


if __name__ == "__main__":
    main()
