"""The App: dispatches a resolved AppConfig to the behavior its command names."""

from __future__ import annotations

from typani.app.config import AppConfig
from typani.logging import get_logger

_log = get_logger(__name__)


# frob:doc docs/cli.md#app
# frob:tests tests/test_cli.py::test_app_runs_the_lint_command
# frob:ticket T-0037
class App:
    """Bind a resolved AppConfig and run its command when called."""

    def __init__(self, cfg: AppConfig) -> None:
        """Store cfg for the eventual __call__ dispatch; performs no work itself."""
        self._cfg = cfg

    # frob:tests tests/test_cli.py::test_app_runs_the_lint_command
    # frob:ticket T-0037
    def __call__(self) -> int:
        """Dispatch on cfg.command; return the process exit code."""
        _log.info("app: dispatching command %r", self._cfg.command)
        if self._cfg.command == "lint":
            return self._run_lint()
        # Unreachable through the CLI: argparse rejects an unknown subcommand
        # before AppConfig is ever built. Reached only by constructing an
        # AppConfig by hand, which from_external exists to discourage.
        _log.error("app: no runner for command %r", self._cfg.command)
        return 2

    def _run_lint(self) -> int:
        """Run the misuse checker with the resolved lint options."""
        # Deferred so `typani --version` and a config error never pay for
        # importing the ast-walking checker.
        from typani.lint.__main__ import run

        return run(self._cfg.lint)
