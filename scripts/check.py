"""Local gate: frob check plus the test suite under both typani backends.

CI cannot run frob until frob has a PyPI release, so this script is the
one command that must be green before a commit: `uv run python
scripts/check.py` (or `make check`). frob check covers ruff, ty, and the
obligation gates; the two pytest runs prove native/pure parity.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import configure_logging, parse_common, repo_root, run  # noqa: E402

logger = logging.getLogger("scripts.check")


def build_parser() -> argparse.ArgumentParser:
    """CLI: --skip-frob for hosts without frob, --skip-tests for gate-only runs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-frob",
        action="store_true",
        help="do not run frob check (hosts without frob on PATH)",
    )
    parser.add_argument("--skip-tests", action="store_true", help="run only frob check")
    parse_common(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run every local gate in order; the first failure stops the run."""
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    root = repo_root()
    if not args.skip_frob:
        logger.info("gate 1/3: frob check")
        run(["frob", "check"], cwd=root, dry_run=args.dry_run)
    if not args.skip_tests:
        pytest = ["uv", "run", "pytest", "-q", "-n", "2"]
        logger.info("gate 2/3: pytest (active backend)")
        run(pytest, cwd=root, dry_run=args.dry_run)
        logger.info("gate 3/3: pytest (TYPANI_PURE=1)")
        run(
            pytest,
            cwd=root,
            dry_run=args.dry_run,
            env={**os.environ, "TYPANI_PURE": "1"},
        )
    logger.info("all local gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
