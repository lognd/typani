"""CLI entry point: ``python -m typani.lint [PATHS...]``."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from typani.lint import JSON_VERSION, Finding, Report, check_tree
from typani.lint._report import render_json, render_text

_log = logging.getLogger(__name__)


# frob:doc docs/lint.md#build_parser
# frob:ticket T-0011
def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the ``typani.lint`` CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m typani.lint",
        description="stdlib-only misuse checker for typani Result/Option usage",
    )
    parser.add_argument(
        "paths", nargs="*", default=["."], help="files or directories to scan"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit a JSON array instead of text"
    )
    parser.add_argument(
        "--exclude", action="append", default=[], help="glob to exclude (repeatable)"
    )
    parser.add_argument(
        "--select", action="append", default=[], help="only keep this rule id"
    )
    parser.add_argument(
        "--ignore", action="append", default=[], help="drop this rule id"
    )
    parser.add_argument(
        "--no-info", action="store_true", help="hide info-severity findings"
    )
    return parser


def _filter_findings(
    findings: list[Finding],
    *,
    select: list[str],
    ignore: list[str],
    no_info: bool,
) -> list[Finding]:
    """Apply --select/--ignore/--no-info to a raw finding list."""
    result = findings
    if select:
        selected = set(select)
        result = [f for f in result if f.rule in selected]
    if ignore:
        ignored = set(ignore)
        result = [f for f in result if f.rule not in ignored]
    if no_info:
        result = [f for f in result if f.severity != "info"]
    return result


# frob:doc docs/lint.md#main
# frob:ticket T-0011
def main(argv: list[str] | None = None) -> int:
    """Run the CLI: scan, filter, print a report, and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = [Path(p) for p in args.paths]
    _log.info("main: scanning %s (exclude=%s)", paths, args.exclude)
    report = check_tree(paths, exclude=args.exclude)

    if report.files_scanned == 0:
        _log.warning("typani.lint: no Python files matched %s", paths)

    gate_findings = _filter_findings(
        report.findings, select=args.select, ignore=args.ignore, no_info=False
    )
    display_findings = (
        [f for f in gate_findings if f.severity != "info"]
        if args.no_info
        else gate_findings
    )

    if args.json:
        display_report = Report(
            version=JSON_VERSION,
            files_scanned=report.files_scanned,
            findings=display_findings,
        )
        print(render_json(display_report))
    else:
        text = render_text(display_findings)
        if text:
            print(text)

    error_count = sum(1 for f in gate_findings if f.severity == "error")
    info_count = sum(1 for f in gate_findings if f.severity == "info")
    print(
        f"typani.lint: {error_count} error(s), {info_count} info(s) in "
        f"{report.files_scanned} file(s) scanned",
        file=sys.stderr,
    )
    _log.info(
        "main: %d error(s), %d info(s) across %d file(s) scanned",
        error_count,
        info_count,
        report.files_scanned,
    )
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
