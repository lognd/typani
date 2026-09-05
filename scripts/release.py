"""Release front door: bump, commit, clean, build, and publish to PyPI.

Native wheels for other platforms come from .github/workflows/release.yml
(cibuildwheel-style matrix builds) -- this script only builds the pure
distribution and, with --native, the native wheel for the current
platform. Run with --dry-run to print every command without touching
the working tree, git, or the network.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import clean as clean_script
from _common import configure_logging, parse_common, repo_root, run
from bump_version import (
    _bump,
    _read_current_version,
    _write_cargo_toml_version,
    _write_init_version,
    _write_native_pyproject_version,
    _write_pyproject_version,
)

import build as build_script

logger = logging.getLogger(__name__)

PUBLISH_TOKEN_VAR = "UV_PUBLISH_TOKEN"


def _git_status_porcelain(root: Path) -> str:
    """Return `git status --porcelain` output, the dirty-tree check's input."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _refuse_if_dirty(root: Path, *, allow_dirty: bool) -> None:
    """Exit 1 if the git tree has uncommitted changes, unless allow_dirty is set."""
    status = _git_status_porcelain(root)
    if status.strip() and not allow_dirty:
        logger.error(
            "git tree is dirty, refusing to release (pass --allow-dirty to override)"
        )
        raise SystemExit(1)
    if status.strip():
        logger.warning("git tree is dirty, proceeding because --allow-dirty was passed")


def _compute_bump(part: str | None, set_version: str | None) -> str:
    """Compute the new version string from --bump/--set, without writing files."""
    current = _read_current_version()
    if set_version is not None:
        return set_version
    assert part is not None
    return _bump(current, part)


def _apply_bump(new_version: str, *, dry_run: bool, root: Path) -> None:
    """Rewrite the coupled version files and commit the bump."""
    if dry_run:
        logger.info("would bump version to %s and commit", new_version)
        return
    _write_pyproject_version(new_version)
    _write_native_pyproject_version(new_version)
    _write_cargo_toml_version(new_version)
    _write_init_version(new_version)
    run(["git", "add", "pyproject.toml"], cwd=root, dry_run=False)
    run(
        ["git", "commit", "-m", f"chore: bump version to {new_version}"],
        cwd=root,
        dry_run=False,
    )


def _resolve_publish_token() -> str:
    """Resolve UV_PUBLISH_TOKEN from the environment, loading .env if possible.

    Never logs or prints the token itself -- only whether it was found.
    """
    import os

    try:
        import dotenv

        dotenv.load_dotenv()
        logger.debug("python-dotenv available, loaded .env if present")
    except ImportError:
        logger.debug("python-dotenv not installed, relying on the process environment")

    token = os.environ.get(PUBLISH_TOKEN_VAR)
    if not token:
        logger.error(
            "%s is not set; export it or install python-dotenv and add it to .env",
            PUBLISH_TOKEN_VAR,
        )
        raise SystemExit(1)
    logger.info("%s is set, proceeding to publish", PUBLISH_TOKEN_VAR)
    return token


def _publish(root: Path, *, dry_run: bool) -> None:
    """Publish dist/* to PyPI via `uv publish`, refusing without a token.

    The token check runs even in --dry-run: a dry run is meant to prove
    the release plan is publishable, not to skip the one check that
    would otherwise fail in a real run.
    """
    logger.info("+ uv publish dist/*")
    _resolve_publish_token()
    if dry_run:
        logger.info("(dry run: publish not executed)")
        return
    run(["uv", "publish"] + sorted(str(p) for p in (root / "dist").glob("*")), cwd=root)


def _tag_and_push(
    root: Path, version: str, *, tag: bool, push: bool, dry_run: bool
) -> None:
    """Create an annotated vX.Y.Z tag and/or push main and the tag."""
    if tag:
        run(
            ["git", "tag", "-a", f"v{version}", "-m", f"v{version}"],
            cwd=root,
            dry_run=dry_run,
        )
    if push:
        run(["git", "push", "origin", "main"], cwd=root, dry_run=dry_run)
        if tag:
            run(["git", "push", "origin", f"v{version}"], cwd=root, dry_run=dry_run)


def main() -> None:
    """Parse args and drive the release: bump, commit, clean, build, publish."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bump", choices=["patch", "minor", "major"], default=None)
    parser.add_argument("--set", dest="set_version", default=None)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument(
        "--native", action="store_true", help="also build a native wheel"
    )
    parser.add_argument(
        "--tag", action="store_true", help="create an annotated vX.Y.Z tag"
    )
    parser.add_argument("--push", action="store_true", help="push main and the tag")
    parse_common(parser)
    args = parser.parse_args()
    configure_logging(args.verbose)

    if args.bump is not None and args.set_version is not None:
        logger.error("--bump and --set are mutually exclusive")
        raise SystemExit(1)

    root = repo_root()

    _refuse_if_dirty(root, allow_dirty=args.allow_dirty)

    version = _read_current_version()
    if args.bump is not None or args.set_version is not None:
        version = _compute_bump(args.bump, args.set_version)
        logger.info("bumping version to %s", version)
        _apply_bump(version, dry_run=args.dry_run, root=root)

    clean_script._remove(root / "dist", dry_run=args.dry_run)
    clean_script._remove(root / "build", dry_run=args.dry_run)

    build_argv = ["uv", "build"]
    run(build_argv, cwd=root, dry_run=args.dry_run)
    if args.native:
        manifest = root / build_script.NATIVE_MANIFEST
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
                    build_script.NATIVE_MANIFEST,
                    "-o",
                    "dist",
                ],
                cwd=root,
                dry_run=args.dry_run,
            )

    _publish(root, dry_run=args.dry_run)

    _tag_and_push(root, version, tag=args.tag, push=args.push, dry_run=args.dry_run)

    print(
        "reminder: native wheels for other platforms are built by "
        ".github/workflows/release.yml, not this script"
    )


if __name__ == "__main__":
    main()
