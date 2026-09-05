"""Text and JSON rendering of typani.lint Finding lists."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typani.lint import Finding, Report

_log = logging.getLogger(__name__)


# frob:doc docs/lint.md#render_text
# frob:ticket T-0011
def render_text(findings: list["Finding"]) -> str:
    """Render findings as 'path:line:col: RULE message' lines, errors before infos."""
    errors = sorted(
        (f for f in findings if f.severity == "error"),
        key=lambda f: (f.path, f.line, f.col),
    )
    infos = sorted(
        (f for f in findings if f.severity != "error"),
        key=lambda f: (f.path, f.line, f.col),
    )
    lines = [_format_line(f) for f in (*errors, *infos)]
    _log.debug("render_text: %d error(s), %d info(s)", len(errors), len(infos))
    return "\n".join(lines)


def _format_line(finding: "Finding") -> str:
    """Format one finding as 'path:line:col: RULE message'."""
    return (
        f"{finding.path}:{finding.line}:{finding.col}: {finding.rule} {finding.message}"
    )


# frob:doc docs/lint.md#render_json
# frob:ticket T-0018
def render_json(report: "Report") -> str:
    """Render a Report as the versioned JSON envelope, preserving finding order."""
    payload = {
        "version": report.version,
        "files_scanned": report.files_scanned,
        "findings": [
            {
                "rule": f.rule,
                "path": f.path,
                "line": f.line,
                "col": f.col,
                "message": f.message,
                "severity": f.severity,
                "symref": f.symref,
            }
            for f in report.findings
        ],
    }
    _log.debug(
        "render_json: version=%d files_scanned=%d findings=%d",
        report.version,
        report.files_scanned,
        len(report.findings),
    )
    return json.dumps(payload, indent=2)
