"""CLI entry point: argparse -> AppConfig.from_external -> App.

``uv tool install typani`` and ``uvx typani`` need an executable to
install; a package with no ``[project.scripts]`` entry point is rejected
as "not a tool package" (T-0037). typani's shippable CLI is the misuse
checker, so it lands here as ``typani lint`` -- while ``python -m
typani.lint`` keeps working as the flags-only module form.
"""

from __future__ import annotations

import argparse
import sys

from typani._version import __version__
from typani.app import App, AppConfig
from typani.app.config import bootstrap_log_level
from typani.lint.__main__ import add_lint_arguments
from typani.logging import configure, get_logger

_log = get_logger(__name__)


# frob:doc docs/cli.md#build_parser
# frob:tests tests/test_cli.py::test_log_level_accepted_on_either_side_of_the_subcommand
# frob:ticket T-0037
def build_parser() -> argparse.ArgumentParser:
    """Build the `typani` subcommand parser tree.

    The lint flags come from `typani.lint`'s own `add_lint_arguments`, so
    the two entry points can never drift apart on what `--select` means.
    """
    # Carried by both the top-level parser and every subparser, so
    # `typani --log-level debug lint src` and `typani lint --log-level debug src`
    # mean the same thing instead of one of them being a usage error.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--log-level",
        dest="log_level",
        # SUPPRESS, not None: a subparser writes its own defaults over the
        # namespace the top-level parser already filled, so a plain default
        # here would erase `typani --log-level X lint ...`.
        default=argparse.SUPPRESS,
        help="minimum level for typani's own diagnostics (default: warning)",
    )

    parser = argparse.ArgumentParser(
        prog="typani", description="typani developer CLI", parents=[common]
    )
    parser.add_argument("--version", action="version", version=f"typani {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    lint = sub.add_parser(
        "lint",
        parents=[common],
        help="run the typani Result/Option misuse checker",
        description="stdlib-only misuse checker for typani Result/Option usage",
    )
    add_lint_arguments(lint)
    return parser


# frob:doc docs/cli.md#main
# frob:tests tests/test_cli.py::test_lint_subcommand_reports_errors
# frob:tests tests/test_cli.py::test_no_subcommand_is_a_config_error
# frob:ticket T-0037
def main(argv: list[str] | None = None) -> int:
    """Parse argv, resolve an AppConfig, and run App(); 2 on a usage/config error."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure before from_external so the config layer's own diagnostics
    # are visible; re-applied afterwards once the resolved level is known.
    configure(bootstrap_log_level(args))

    result = AppConfig.from_external(args)
    if not result.is_ok:
        _log.error("configuration error: %s", result.danger_err)
        if args.command is None:
            parser.print_help(sys.stderr)
        return 2

    cfg = result.danger_ok
    configure(cfg.log_level)
    _log.debug("main: running %r", cfg)
    return App(cfg)()


if __name__ == "__main__":
    raise SystemExit(main())
