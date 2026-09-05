"""Bootstrap the project's dependencies with `uv sync`.

No stamp file: `uv sync` is already incremental (it checks pyproject.toml
and uv.lock hashes itself), so a Makefile stamp guard on top of it is
redundant bookkeeping that can drift out of sync with the real state.
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
    """Parse args and run `uv sync --all-groups` (optionally `--all-extras`)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extras",
        action="store_true",
        help="also pass --all-extras (pulls in the native typani-core extra)",
    )
    parse_common(parser)
    args = parser.parse_args()
    configure_logging(args.verbose)

    argv = ["uv", "sync", "--all-groups"]
    if args.extras:
        argv.append("--all-extras")

    run(argv, cwd=repo_root(), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
