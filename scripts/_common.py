"""Shared helpers for scripts/*.py: repo root, logging, and a logged run() wrapper.

Keeps the Makefile-owner rule honest -- every Makefile target is a one-line
`uv run python scripts/<name>.py` call, so the scripts themselves need one
home for the argv-logging subprocess wrapper and the --dry-run/-v flag
convention instead of each script re-inventing it.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def repo_root() -> Path:
    """Return the repository root (the parent of this scripts/ directory)."""
    return Path(__file__).resolve().parent.parent


def configure_logging(verbose: bool) -> None:
    """Attach a plain stderr handler to the root logger at INFO or DEBUG."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def parse_common(parser: argparse.ArgumentParser) -> None:
    """Add the shared --dry-run and -v/--verbose flags to a script's parser."""
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the commands that would run without executing them",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable debug-level logging",
    )


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    dry_run: bool = False,
    env: dict[str, str] | None = None,
) -> None:
    """Log and execute argv, raising SystemExit(returncode) on failure.

    When dry_run is set, only logs the command and returns without
    executing it -- callers rely on this for --dry-run flows across all
    scripts.
    """
    logger.info("+ %s", " ".join(argv))
    if dry_run:
        return
    result = subprocess.run(argv, cwd=cwd, env=env)
    if result.returncode != 0:
        logger.error("command failed (exit %d): %s", result.returncode, " ".join(argv))
        raise SystemExit(result.returncode)
