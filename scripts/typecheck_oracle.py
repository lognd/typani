"""Run mypy against mypy-py310.ini, the 3.10-semantics oracle alongside ty.

frob check runs ty as the primary type checker; this script is the
secondary oracle cross-check kept outside frob (bootstrap/build-adjacent
tooling, see the Makefile's own comment on why).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import configure_logging, parse_common, repo_root, run

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse args and run `uv run mypy --config-file mypy-py310.ini`."""
    parser = argparse.ArgumentParser(description=__doc__)
    parse_common(parser)
    args = parser.parse_args()
    configure_logging(args.verbose)

    run(
        ["uv", "run", "mypy", "--config-file", "mypy-py310.ini"],
        cwd=repo_root(),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
