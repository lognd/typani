"""Build the optional native crate in place with `maturin develop`.

If crates/typani-core/Cargo.toml does not exist yet (T-0010), logs a
warning and exits 0 rather than failing -- the native crate is optional
and most contributors never need it.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import configure_logging, parse_common, repo_root, run

logger = logging.getLogger(__name__)

CRATE_MANIFEST = "crates/typani-core/Cargo.toml"


def main() -> None:
    """Parse args and run `uv run maturin develop` against the native crate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="build a debug extension instead of the default --release",
    )
    parse_common(parser)
    args = parser.parse_args()
    configure_logging(args.verbose)

    root = repo_root()
    manifest = root / CRATE_MANIFEST
    if not manifest.exists():
        logger.warning(
            "%s does not exist yet (T-0010), skipping develop build", manifest
        )
        raise SystemExit(0)

    argv = ["uv", "run", "maturin", "develop", "--uv", "-m", CRATE_MANIFEST]
    if not args.debug:
        argv.append("--release")

    run(argv, cwd=root, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
