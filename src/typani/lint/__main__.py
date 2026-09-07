"""CLI entry point: ``python -m typani.lint [PATHS...]``.

The same code backs the ``typani lint`` console script (T-0037): that
path resolves an :class:`~typani.lint.options.LintOptions` through
``typani.app.config.AppConfig``'s layering and calls :func:`run` directly,
so the flags below are defined, and the scan is executed, in exactly one
place regardless of how the checker was invoked.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from typani.lint import JSON_VERSION, Finding, Report, check_tree
from typani.lint._report import render_json, render_text
from typani.lint.options import LintOptions, namespace_to_mapping
from typani.logging import get_logger

_log = get_logger(__name__)


# frob:doc docs/lint.md#build_parser
# frob:ticket T-0011
# frob:tests tests/test_cli.py::test_lint_subcommand_forwards_flags
# frob:ticket T-0037
def add_lint_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Define the lint flags on `parser` and return it.

    Every default is `None` rather than a real value: `None` is argparse's
    "the user did not pass this" marker, which is what lets AppConfig layer
    a config file and environment variables *underneath* these flags. The
    real defaults live once, on `LintOptions`.
    """
    parser.add_argument(
        "paths", nargs="*", default=None, help="files or directories to scan"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=None,
        help="emit a JSON envelope instead of text",
    )
    parser.add_argument(
        "--exclude", action="append", default=None, help="glob to exclude (repeatable)"
    )
    parser.add_argument(
        "--select", action="append", default=None, help="only keep this rule id"
    )
    parser.add_argument(
        "--ignore", action="append", default=None, help="drop this rule id"
    )
    parser.add_argument(
        "--no-info",
        action="store_true",
        default=None,
        help="hide info-severity findings",
    )
    return parser


# frob:doc docs/lint.md#build_parser
# frob:ticket T-0011
# frob:ticket T-0037
def build_parser(prog: str = "python -m typani.lint") -> argparse.ArgumentParser:
    """Build the standalone parser for the module-form CLI under `prog`."""
    return add_lint_arguments(
        argparse.ArgumentParser(
            prog=prog,
            description="stdlib-only misuse checker for typani Result/Option usage",
        )
    )


def _filter_findings(
    findings: list[Finding],
    *,
    select: tuple[str, ...],
    ignore: tuple[str, ...],
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


# frob:doc docs/lint.md#run
# frob:tests tests/test_cli.py::test_app_runs_the_lint_command
# frob:ticket T-0037
def run(options: LintOptions) -> int:
    """Scan, filter, print a report, and return the process exit code.

    The single execution path shared by `python -m typani.lint` and
    `typani lint`; everything above it is argument resolution.
    """
    paths = [Path(p) for p in options.paths]
    _log.info("run: scanning %s (exclude=%s)", paths, list(options.exclude))
    report = check_tree(paths, exclude=list(options.exclude))

    if report.files_scanned == 0:
        _log.warning("typani.lint: no Python files matched %s", paths)

    gate_findings = _filter_findings(
        report.findings, select=options.select, ignore=options.ignore, no_info=False
    )
    display_findings = (
        [f for f in gate_findings if f.severity != "info"]
        if options.no_info
        else gate_findings
    )

    if options.json:
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
        "run: %d error(s), %d info(s) across %d file(s) scanned",
        error_count,
        info_count,
        report.files_scanned,
    )
    return 1 if error_count else 0


# frob:doc docs/lint.md#main
# frob:ticket T-0011
def main(argv: list[str] | None = None, *, prog: str | None = None) -> int:
    """Run the module-form CLI: parse argv into LintOptions and run the scan.

    Unlike `typani lint`, this path applies no config-file or environment
    layer -- `python -m typani.lint` is the flags-only invocation.
    """
    parser = build_parser() if prog is None else build_parser(prog)
    args = parser.parse_args(argv)
    options = LintOptions.from_mapping(namespace_to_mapping(args))
    _log.debug("main: resolved %r", options)
    return run(options)


if __name__ == "__main__":
    from typani.logging import configure

    configure()
    raise SystemExit(main())
