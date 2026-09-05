"""Bump typani's version across pyproject.toml, the native crate, and _version.py.

Keeps pyproject.toml's `version`, crates/typani-core/pyproject.toml and
Cargo.toml (when the native crate exists, T-0010), and
src/typani/_version.py's `__version__` literal all in lockstep -- the
version-coupling doctrine documented in pyproject.toml's `native` extra
comment. Prints only the resulting version to stdout (CLI output);
everything else goes through `logging`.
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 has no stdlib tomllib.
    import tomli as tomllib  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT_PY = ROOT / "src" / "typani" / "_version.py"
NATIVE_PYPROJECT = ROOT / "crates" / "typani-core" / "pyproject.toml"
NATIVE_CARGO_TOML = ROOT / "crates" / "typani-core" / "Cargo.toml"

VERSION_RE = re.compile(r"^version = \"(\d+)\.(\d+)\.(\d+)\"", re.M)
INIT_VERSION_RE = re.compile(r'^__version__ = "[^"]+"', re.M)
CARGO_VERSION_RE = re.compile(r'^version = "[^"]+"', re.M)


def _bump(current: str, part: str) -> str:
    """Compute the next version string for the given part (major/minor/patch)."""
    major, minor, patch = (int(x) for x in current.split("."))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def _read_current_version() -> str:
    """Read the current version from pyproject.toml's [project] table."""
    with PYPROJECT.open("rb") as f:
        data = tomllib.load(f)
    version = data["project"]["version"]
    logger.debug("current pyproject.toml version: %s", version)
    return version


def _write_pyproject_version(new: str) -> None:
    """Rewrite the top-level pyproject.toml's version in place."""
    text = PYPROJECT.read_text()
    text, count = VERSION_RE.subn(f'version = "{new}"', text, count=1)
    if count != 1:
        logger.error("failed to find version in %s", PYPROJECT)
        raise SystemExit(1)
    PYPROJECT.write_text(text)
    logger.info("updated %s", PYPROJECT)


def _write_init_version(new: str) -> None:
    """Rewrite src/typani/_version.py's __version__ literal in place."""
    if not INIT_PY.exists():
        logger.warning("%s does not exist, skipping", INIT_PY)
        return
    text = INIT_PY.read_text()
    text, count = INIT_VERSION_RE.subn(f'__version__ = "{new}"', text, count=1)
    if count != 1:
        logger.warning("no __version__ literal found in %s, skipping", INIT_PY)
        return
    INIT_PY.write_text(text)
    logger.info("updated %s", INIT_PY)


def _write_native_pyproject_version(new: str) -> None:
    """Rewrite crates/typani-core/pyproject.toml's version, if the crate exists."""
    if not NATIVE_PYPROJECT.exists():
        logger.debug("%s does not exist yet (T-0010), skipping", NATIVE_PYPROJECT)
        return
    text = NATIVE_PYPROJECT.read_text()
    text, count = VERSION_RE.subn(f'version = "{new}"', text, count=1)
    if count != 1:
        logger.error("failed to find version in %s", NATIVE_PYPROJECT)
        raise SystemExit(1)
    NATIVE_PYPROJECT.write_text(text)
    logger.info("updated %s", NATIVE_PYPROJECT)


def _write_cargo_toml_version(new: str) -> None:
    """Rewrite crates/typani-core/Cargo.toml's [package] version, if it exists."""
    if not NATIVE_CARGO_TOML.exists():
        logger.debug("%s does not exist yet (T-0010), skipping", NATIVE_CARGO_TOML)
        return
    text = NATIVE_CARGO_TOML.read_text()
    text, count = CARGO_VERSION_RE.subn(f'version = "{new}"', text, count=1)
    if count != 1:
        logger.error("failed to find version in %s", NATIVE_CARGO_TOML)
        raise SystemExit(1)
    NATIVE_CARGO_TOML.write_text(text)
    logger.info("updated %s", NATIVE_CARGO_TOML)


def main() -> None:
    """Parse args, compute the new version, and rewrite every coupled file."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part",
        choices=["major", "minor", "patch"],
        default="patch",
        help="version component to bump (default: patch)",
    )
    parser.add_argument(
        "--set",
        dest="set_version",
        default=None,
        help="set an explicit X.Y.Z version instead of bumping",
    )
    args = parser.parse_args()

    current = _read_current_version()

    if args.set_version is not None:
        if not re.fullmatch(r"\d+\.\d+\.\d+", args.set_version):
            logger.error("--set expects X.Y.Z, got %r", args.set_version)
            raise SystemExit(1)
        new = args.set_version
    else:
        new = _bump(current, args.part)

    logger.info("bumping version %s -> %s", current, new)

    _write_pyproject_version(new)
    _write_native_pyproject_version(new)
    _write_cargo_toml_version(new)
    _write_init_version(new)

    print(new)


if __name__ == "__main__":
    main()
