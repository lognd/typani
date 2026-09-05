"""Remove build/test artifacts with shutil/pathlib only (no shell rm/find).

Platform-agnostic replacement for the Makefile's old `rm -rf`/`find -exec`
recipe, so Windows contributors can run `uv run python scripts/clean.py`
directly.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import configure_logging, parse_common, repo_root

logger = logging.getLogger(__name__)

FIXED_TARGETS = (
    "dist",
    "build",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".ty_cache",
    "htmlcov",
    "coverage.xml",
    ".coverage",
)

SKIP_DIR_NAMES = {".venv", ".git"}
NATIVE_TARGET_DIR = "crates/typani-core/target"


def _remove(path: Path, *, dry_run: bool) -> None:
    """Remove a single file or directory tree, logging and printing its path."""
    if not path.exists():
        return
    logger.info("removing %s", path)
    print(path)
    if dry_run:
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _iter_glob_targets(root: Path, pattern: str) -> list[Path]:
    """Find every directory under root matching pattern, skipping excluded trees."""
    matches: list[Path] = []
    for candidate in root.rglob(pattern):
        if not candidate.is_dir():
            continue
        relative_parts = candidate.relative_to(root).parts
        if any(part in SKIP_DIR_NAMES for part in relative_parts):
            continue
        if relative_parts[0] == "crates" and "target" in relative_parts:
            continue
        matches.append(candidate)
    return matches


def main() -> None:
    """Parse args and remove build artifacts under the repo root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--native",
        action="store_true",
        help="also remove crates/typani-core/target",
    )
    parse_common(parser)
    args = parser.parse_args()
    configure_logging(args.verbose)

    root = repo_root()

    for name in FIXED_TARGETS:
        _remove(root / name, dry_run=args.dry_run)

    for pattern in ("__pycache__", "*.egg-info"):
        for match in _iter_glob_targets(root, pattern):
            _remove(match, dry_run=args.dry_run)

    if args.native:
        _remove(root / NATIVE_TARGET_DIR, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
