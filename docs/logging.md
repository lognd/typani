<!-- frob:describes src/typani/logging/logger.py::get_logger -->

# Logging

<a id="get_logger"></a>

Every module in typani logs through one channel -- `get_logger`, defined
in `src/typani/logging/logger.py`:

<!-- frob:describes src/typani/logging/logger.py::get_logger -->

```python
from typani.logging import get_logger

_log = get_logger(__name__)
```

No `print()` for diagnostics. The only `print()` calls in the package are
the checker's intentional CLI output -- the finding lines and the summary
line, which are the tool's product, not its instrumentation.

## Why this is split in two

typani is a **library** first. A library that calls
`logging.config.dictConfig` at import time hijacks the logging setup of
whatever application imported it, which is why `get_logger` here does
nothing but name a logger:

```python
get_logger(name: str) -> logging.Logger
```

Returns `logging.getLogger(name)`. Attaches no handlers, installs no
config, and has no import-time side effects. Importing `typani`,
`typani.lint` or anything else in the package therefore leaves the
consuming application's logging exactly as it found it.

<a id="configure"></a>

```python
configure(level: str | None = None) -> None
```

Installs the handlers, and is called from exactly one place:
`typani.__main__.main`, the CLI entry point, where typani *is* the
application and owns its own output. It is idempotent -- a second call
re-applies only the level, so it cannot stack duplicate handlers -- and
an unrecognized `level` is warned about and ignored rather than raised,
because it runs before `AppConfig.from_external` has had the chance to
report it as `ConfigError.BadLogLevel`, and a bad `--log-level` must not
surface as a traceback.

This is where typani deviates from the sibling CLI repos, whose
`get_logger` initializes on first call. They are applications; typani is
a library that happens to ship one.

`configure` only ever touches the `typani` logger, never the root
logger, and sets `propagate = False` on it -- so even a consuming
application that *did* call `configure` keeps its own root handlers
unpolluted.

<a id="logging-config"></a>

## The config

`typani/logging/config.py` holds `LOGGING_CONFIG`, the `dictConfig`
payload:

- DEBUG/INFO go to **stdout**, WARNING and above to **stderr**
  (`BelowLevelFilter` keeps the two from overlapping). A `--json` scan's
  machine-readable stdout is therefore never interleaved with
  diagnostics at the default level.
- `TypaniFormatter` prints WARNING+ as `LEVEL: message` and everything
  below it as the bare message.
- The default level is `WARNING`, so the CLI is quiet unless asked
  otherwise (`--log-level info`, `TYPANI_LOG_LEVEL=debug`, or
  `log_level` under `[tool.typani]`).

It is a Python dict rather than the usual sibling-repo `config.toml`:
typani supports 3.10, where `tomllib` does not exist, and its runtime
dependency list is empty by contract, so it cannot reach for `tomli` just
to read its own logging config. `dictConfig` consumes a dict anyway, so
this is the same single source of truth in the format the stdlib wants.

## See also

- [cli.md](cli.md) -- the entry point that calls `configure`
