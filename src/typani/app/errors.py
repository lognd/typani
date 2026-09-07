"""Typed failures the CLI's configuration layer can hand back to __main__."""

from __future__ import annotations

from typani.error_set import ErrorSet


# frob:doc docs/cli.md#configerror
# frob:tests tests/test_cli.py::test_from_external_reports_a_missing_subcommand
# frob:ticket T-0037
class ConfigError(ErrorSet):
    """Why a CLI invocation could not be resolved into an AppConfig."""

    NoCommand = "no subcommand given"
    BadLogLevel = "log level is not a logging level name"
    BadConfigFile = "pyproject.toml did not parse as TOML"
    BadConfigValue = "a [tool.typani.lint] value has the wrong type"
