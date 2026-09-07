<!-- frob:describes src/typani/__main__.py::main -->

# The `typani` CLI

`typani` is the console script this package installs
(`src/typani/__main__.py`, wired up as `[project.scripts] typani =
"typani.__main__:main"`). It exists for a packaging reason as much as a
usability one: `uv tool install typani` and `uvx typani` reject a
distribution that ships no executable, so before T-0037 the checker was
reachable only as `python -m typani.lint`, from inside an environment
that already had typani installed.

```console
$ uvx typani lint src                        # no install, one-shot
$ uv tool install typani && typani lint src  # installed on PATH
$ pipx run typani lint src                   # same, via pipx
$ python -m typani lint src                  # module form of the same entry
$ python -m typani.lint src                  # flags-only module form (no config layering)
```

`lint` is currently the only subcommand; see [lint.md](lint.md) for its
flags, rules and exit codes. `typani --version` prints the installed
version, and `typani` with no subcommand prints usage and exits `2`.

## Architecture

The entry point follows the App/AppConfig shape the sibling CLI repos
use: parse argv, resolve one immutable config, hand it to an App.

```
typani/__main__.py   argparse -> configure logging -> AppConfig.from_external -> App(cfg)()
typani/app/config.py AppConfig, the layered settings, and its ConfigError values
typani/app/app.py    App, the command -> runner dispatch
typani/lint/         the checker itself; App calls its run(), never the reverse
```

The dependency direction is deliberate. `typani.app` imports
`typani.lint`; `typani.lint` imports nothing from typani proper, which is
the isolation constraint `design/typani.strata` enforces (`python -m
typani.lint` must not drag in `Result`, `Option` or the backend
selector). That is also why `LintOptions` lives in `typani/lint/options.py`
as a plain stdlib dataclass and does no validation -- everything fallible
happens one layer up, in `AppConfig`, where typani's own `Result` is
available.

<a id="build_parser"></a>

### `build_parser`

```python
build_parser() -> argparse.ArgumentParser
```

Builds the subcommand tree. The lint flags are not redefined here: it
calls `typani.lint.__main__.add_lint_arguments`, so `typani lint` and
`python -m typani.lint` cannot drift apart on what a flag means.

`--log-level` is attached to the top-level parser *and* to every
subparser (via an `add_help=False` parent whose default is
`argparse.SUPPRESS`), so `typani --log-level debug lint src` and `typani
lint --log-level debug src` are the same invocation. The `SUPPRESS`
default matters: argparse writes a subparser's defaults over the
namespace the top-level parser already filled, so a plain `None` default
would silently erase the flag when it was given before the subcommand.

<a id="main"></a>

### `main`

```python
main(argv: list[str] | None = None) -> int
```

Parses argv, installs the logging channel, resolves an `AppConfig`, and
runs `App(cfg)()`. Returns the runner's exit code, or `2` for a usage or
configuration error (a missing subcommand, an unknown `--log-level`, an
unparseable `pyproject.toml`).

<a id="appconfig"></a>

## `AppConfig`

```python
@dataclass(frozen=True, slots=True)
class AppConfig:
    command: str = "lint"
    log_level: str = "WARNING"
    lint: LintOptions = LintOptions()

    @classmethod
    def from_external(
        cls, args: argparse.Namespace, config_file: Path | None = None
    ) -> Result[AppConfig, ConfigError]: ...
```

`from_external` is the only public constructor: it is where the
precedence rules live, so building an `AppConfig` by hand skips them.
Precedence, highest first:

| Layer | Source |
|-------|--------|
| CLI flags | the parsed `argparse.Namespace` |
| environment | `TYPANI_LOG_LEVEL`, `TYPANI_LINT_PATHS`, `TYPANI_LINT_EXCLUDE`, `TYPANI_LINT_SELECT`, `TYPANI_LINT_IGNORE` (comma-separated for the list-valued ones) |
| config file | `[tool.typani]` and `[tool.typani.lint]` in `pyproject.toml` |
| defaults | the field defaults above and on `LintOptions` |

```toml
# pyproject.toml
[tool.typani]
log_level = "info"

[tool.typani.lint]
paths = ["src", "tests"]
ignore = ["TYP004"]
no_info = true
```

Two behaviors worth knowing:

- A **missing** config file is not an error -- the file layer is
  optional. An **unparseable** one is `ConfigError.BadConfigFile`.
- On Python 3.10 there is no `tomllib`, and typani's runtime dependency
  list is empty by contract, so it cannot fall back to `tomli`. The file
  layer is skipped there with an INFO log; CLI flags, environment
  variables and defaults all still apply. This is the one documented
  behavior difference between 3.10 and 3.11+.

An `nargs="*"` positional the user omitted arrives from argparse as `[]`,
not `None`. `LintOptions.from_mapping` treats an empty sequence as unset
for exactly this reason -- otherwise a bare `typani lint` would clobber
the `paths` set in `pyproject.toml` with nothing.

`AppConfig` is a frozen dataclass rather than a pydantic `BaseModel`,
which is what the sibling CLI repos use. typani ships with an empty
runtime dependency list (pydantic is an extra), and `uvx typani lint`
must not pull a dependency into a tree that only wanted the checker. The
dataclass plus typani's own `Result` is the dependency-free equivalent --
and dogfoods the library the CLI ships with.

<a id="configerror"></a>

### `ConfigError`

A typani `ErrorSet`; `from_external` returns these as values, never
raises them.

| Member | Meaning |
|--------|---------|
| `NoCommand` | no subcommand was given |
| `BadLogLevel` | `--log-level` / `TYPANI_LOG_LEVEL` is not a logging level name |
| `BadConfigFile` | the config file exists but did not parse as TOML |
| `BadConfigValue` | `[tool.typani]` or `[tool.typani.lint]` is not a table |

<a id="app"></a>

## `App`

```python
class App:
    def __init__(self, cfg: AppConfig) -> None: ...
    def __call__(self) -> int: ...
```

Config in, side effects out. `__call__` dispatches on `cfg.command` and
returns the process exit code; the lint runner is imported inside the
branch that needs it, so `typani --version` and a configuration error
never pay for importing the AST walker.

## See also

- [lint.md](lint.md) -- the checker, its rules and its flags
- [logging.md](logging.md) -- the logging channel `main` installs
