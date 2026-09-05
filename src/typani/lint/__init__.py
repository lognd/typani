"""stdlib-only misuse checker for code that uses typani's Result/Option types.

Run as ``python -m typani.lint [PATHS...]``. This package must never be
imported from ``typani/__init__.py`` -- it stays an opt-in dev tool with
zero runtime footprint on the main package.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from typani.lint._rules import RULES, MisuseVisitor, apply_suppressions, is_skip_file

_log = logging.getLogger(__name__)

_DEFAULT_EXCLUDE_DIRS = frozenset(
    {".venv", ".git", "__pycache__", "node_modules", "build", "dist"}
)

# tests/fixtures/lint/** deliberately contains misuse patterns as lint-rule
# fixtures; it is a lint target for tests/test_lint.py, never for a plain
# `python -m typani.lint` sweep of the tree.
_FIXTURE_LINT_DIR = Path("tests") / "fixtures" / "lint"


# frob:doc docs/lint.md#finding
# frob:ticket T-0011
@dataclass(frozen=True, slots=True)
class Finding:
    """One lint hit: a rule id, its location, and a human-readable message."""

    rule: str
    path: str
    line: int
    col: int
    message: str
    severity: str


__all__ = ["Finding", "RULES", "check_source", "check_paths"]


# frob:doc docs/lint.md#check_source
# frob:ticket T-0011
def check_source(source: str, path: str = "<string>") -> list[Finding]:
    """Lint one Python source string; syntax errors become a single TYP000 Finding."""
    _log.debug("check_source: parsing %s (%d bytes)", path, len(source))
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        _log.warning("check_source: syntax error in %s: %s", path, exc)
        return [
            Finding(
                rule="TYP000",
                path=path,
                line=exc.lineno or 1,
                col=(exc.offset or 1) - 1,
                message=f"syntax error: {exc.msg}",
                severity="error",
            )
        ]

    if is_skip_file(source):
        _log.info("check_source: %s carries 'typani: skip-file', skipping", path)
        return []

    visitor = MisuseVisitor(path=path)
    visitor.visit(tree)
    findings = apply_suppressions(source, visitor.findings)
    _log.debug("check_source: %s produced %d finding(s)", path, len(findings))
    return findings


# frob:doc docs/lint.md#check_paths
# frob:ticket T-0011
def check_paths(paths: Iterable[Path], *, exclude: Iterable[str] = ()) -> list[Finding]:
    """Walk *paths* for ``*.py`` files (skipping vcs/build noise) and lint each one."""
    exclude_globs = list(exclude)
    findings: list[Finding] = []
    for py_file in _iter_python_files(paths, exclude_globs):
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError as exc:
            _log.error("check_paths: could not read %s: %s", py_file, exc)
            continue
        findings.extend(check_source(source, path=str(py_file)))

    findings.sort(key=lambda f: (f.path, f.line, f.col))
    _log.info(
        "check_paths: scanned paths=%s -> %d finding(s)", list(paths), len(findings)
    )
    return findings


def _iter_python_files(
    paths: Iterable[Path], exclude_globs: list[str]
) -> Iterable[Path]:
    """Yield every ``*.py`` file under *paths*, applying default and user excludes."""
    for root in paths:
        if root.is_file():
            candidates: Iterable[Path] = [root] if root.suffix == ".py" else []
        else:
            candidates = root.rglob("*.py")
        for candidate in candidates:
            if _is_excluded(candidate, exclude_globs):
                continue
            yield candidate


def _is_excluded(candidate: Path, exclude_globs: list[str]) -> bool:
    """Return True when *candidate* sits under a default-excluded dir or user glob."""
    if any(part in _DEFAULT_EXCLUDE_DIRS for part in candidate.parts):
        return True
    parts = candidate.parts
    fixture_parts = _FIXTURE_LINT_DIR.parts
    if any(
        parts[i : i + len(fixture_parts)] == fixture_parts
        for i in range(len(parts) - len(fixture_parts) + 1)
    ):
        return True
    return any(candidate.match(pattern) for pattern in exclude_globs)
