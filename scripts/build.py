"""Build distributable packages into dist/ with `uv build` (and maturin with --native).

Prints the resulting file list so `make build` gives visible output on
every platform without shelling out to `ls`.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import configure_logging, parse_common, repo_root, run

logger = logging.getLogger(__name__)

NATIVE_MANIFEST = "crates/typani-core/Cargo.toml"


def main() -> None:
    """Parse args, run uv build (and maturin build with --native), then list dist/."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--native",
        action="store_true",
        help="also build the native wheel with maturin for the current platform",
    )
    parse_common(parser)
    args = parser.parse_args()
    configure_logging(args.verbose)

    root = repo_root()
    dist = root / "dist"

    run(["uv", "build"], cwd=root, dry_run=args.dry_run)

    if args.native:
        manifest = root / NATIVE_MANIFEST
        if not manifest.exists():
            logger.warning(
                "%s does not exist yet (T-0010), skipping native build", manifest
            )
        else:
            run(
                [
                    "uv",
                    "run",
                    "maturin",
                    "build",
                    "--release",
                    "-m",
                    NATIVE_MANIFEST,
                    "-o",
                    "dist",
                ],
                cwd=root,
                dry_run=args.dry_run,
            )

    if args.dry_run:
        return

    if dist.exists():
        for path in sorted(dist.iterdir()):
            print(path)
    else:
        logger.warning("%s does not exist after build", dist)


if __name__ == "__main__":
    main()
