# typani.lint

`python -m typani.lint` (`src/typani/lint/__main__.py`) is a stdlib-only
static checker for code that *uses* typani's `Result`/`Option` types. It
has no dependencies (only `ast`, `argparse`, `json`, `pathlib`, `logging`,
`dataclasses`) and never imports from `typani`'s main package -- it is a
dev-time tool, not a runtime one. `src/typani/lint/_report.py` renders
the JSON/text findings report the CLI prints.

## Why this exists

`docs/redesign-0.1.md` section 1.2 traces a cluster of real bugs back to
a small set of repeatable typani misuse shapes: a property called as a
method (`danger_ok()`), truthiness tests on a payload that can be falsy
(`if r.ok:` misreading `Ok(0)` as failure), a `Result`/`Option` value that
is constructed or chained and then silently discarded, hand-rolled
propagation boilerplate that duplicates what `unwrap()`/`@propagate`
already do, and `assert`-based invariants that vanish under `python -O`.
`typani.lint` turns each of those into a mechanical, CI-checkable rule
(section 2.6 of the same document) instead of relying on review to catch
them again every time.

## Usage

```console
$ python -m typani.lint                      # lint "." by default
$ python -m typani.lint src tests             # lint specific paths
$ python -m typani.lint --json src            # versioned JSON envelope on stdout
$ python -m typani.lint --no-info src         # hide info-severity findings
$ python -m typani.lint --select TYP001 src   # only run one rule
$ python -m typani.lint --ignore TYP004 src   # drop one rule
$ python -m typani.lint --exclude '*/generated/*' src
```

Text output is one line per finding:

```
src/app/queue.py:42:7: TYP002 'ok' is the payload or None; falsy payloads (0, '', []) will be misread -- test 'is_ok' instead
```

Errors are printed before infos; each group is sorted by
`(path, line, col)`. A summary line always goes to **stderr**, for both
text and `--json` output:

```
typani.lint: 2 error(s), 1 info(s) in 37 file(s) scanned
```

### Exit codes

`0` when no error-severity finding survives `--select`/`--ignore`; `1`
otherwise. `--no-info` only changes what is *printed* -- it never changes
the exit code, since info findings never gate the exit code in the first
place.

### `check_tree` walking rules

`*.py` files are found recursively under each given path. `.venv`,
`.git`, `__pycache__`, `node_modules`, `build`, and `dist` directories are
always skipped, as is `tests/fixtures/lint/` in this repo (it holds
deliberate misuse fixtures for `tests/test_lint.py`, not real code).
`--exclude GLOB` (repeatable) adds further glob exclusions, matched with
`pathlib.PurePath.match`.

## Rules

### TYP001 -- property called as a method (error)

`is_ok`, `is_err`, `ok`, `err`, `danger_ok`, `danger_err`, `notes`,
`is_some`, `is_nothing`, `some`, `danger_some`, `value`, and `error` are
all properties. Calling one with zero arguments is almost always a typo
for the property access (`x.danger_ok()` instead of `x.danger_ok`); this
is the single most-repeated typani footgun on record (section 1.2).

```python
# bad
if result.is_ok():
    ...
value = result.danger_ok()

# good
if result.is_ok:
    ...
value = result.danger_ok
```

A call with any positional or keyword argument is left alone, since that
is a strong signal it is an unrelated method on a different object (e.g.
`dict.get()`).

### TYP002 -- truthiness of a payload attribute (error)

`.ok`, `.err`, and `.some` hold the payload itself (or `None`), not a
boolean. `if result.ok:` misreads `Ok(0)`, `Ok("")`, and `Ok([])` as
failure.

```python
# bad
r = Ok(0)
if r.ok:
    ...  # never runs -- 0 is falsy

# good
if r.is_ok:
    ...
```

This rule only fires when the checker has direct local evidence that the
subject is actually a `Result`/`Option`: it is a call to `Ok`/`Err`/
`Some`/`Nothing`, a call to a same-module function/method annotated to
return one, or a name bound to one of those earlier in the same function.
A bare `if report.ok:` on an unannotated parameter is left alone. This
restriction exists because the unrestricted (name-only) version of the
rule is dominated by false positives on real code: scanning frob's
~650-file `src/` tree, matching purely on the attribute name `.ok` (with
no evidence requirement) produced 16 hits, and by-hand inspection showed
**all 16** were unrelated domain objects with their own `.ok` boolean
field (`report.ok`, `crate.ok`, a cached coverage result's `.ok`) rather
than a typani `Result`. Restricting to subjects with local
Result/Option-producing evidence reduced that to 0 false positives while
keeping every genuine typani misuse case reachable through
`check_source`'s own test fixtures. `typani.lint` has no type inference
and never will (stdlib `ast` only) -- this evidence-based restriction is
the deliberate trade-off for staying conservative rather than chasing
every truthy-`.ok` field by name.

### TYP003 -- discarded Result/Option (error)

A `Result`/`Option` that is constructed, returned from a same-module
function, or chained off a combinator, and then never assigned, returned,
or otherwise inspected, is the single largest bug family in section 1.2
("silently dropped/ignored/discarded", 63 changelog titles).

```python
# bad
def save(path: Path) -> "Result[Unit, IOError]":
    ...

save(path)          # the failure is thrown away

r = save(path)
r.map(log_saved)    # r.map(...) allocates a new Result that is also thrown away

# good
result = save(path)
if result.is_err:
    handle(result.danger_err)
```

Flagged shapes, all as a bare expression-statement:

- `Ok(...)`, `Err(...)`, `Some(...)`, `Nothing()`
- a call to a function defined at module level in the same file, or a
  `self.<name>(...)` call to a method defined one level inside a class in
  the same file, whose return annotation (unparsed, forward-reference
  strings included) is `Result[...]`, `Option[...]`, a bare `Result`/
  `Option`, or `typani.result.Result[...]`/`typani.option.Option[...]`
- `<expr>.map(...)`, `.map_err(...)`, `.and_then(...)`, `.or_else(...)`,
  `.note(...)`, `.filter(...)`, `.ok_or(...)`, `.ok_or_else(...)`, or
  `.to_option(...)` where `<expr>` is itself one of the constructor calls
  above, or a name assigned one of those shapes earlier in the same
  function

Assigning the value (`x = Ok(1)`), returning it, or passing it onward is
never flagged -- only the fully-discarded, bare-statement shape is.
`.inspect(...)`/`.inspect_err(...)` are deliberately excluded from this
set: they exist precisely to be called for their side effect with the
return value discarded (Rust's `inspect` idiom), so `Ok(1).inspect(print)`
as a bare statement is correct, not a bug.

### TYP004 -- propagation boilerplate (info, two shapes)

```python
# flagged (informational)
if loaded.is_err:
    return Err(loaded.danger_err)
queue = loaded.danger_ok

# suggested
queue = loaded.unwrap()   # inside a function decorated with @propagate
```

Flags the exact `if X.is_err: return Err(X.danger_err)` shape (and its
`Option` twin, `if X.is_nothing: return Nothing()`) -- see
`docs/redesign-0.1.md` section 1.3 for the Rust-`?`-style propagation
this boilerplate stands in for. Informational only: the boilerplate is
correct, just longer than it needs to be.

A second, related shape is also flagged, with a different message: `if
X.is_err: return Err(<mapped>)` where `<mapped>` is a single call to
`Err` whose argument is *not* `X.danger_err` (e.g. `Err(SomeOtherError())`
or `Err(f(X.danger_err))`, wrapping the error before returning it):

```python
# flagged (informational): mapped error
if loaded.is_err:
    return Err(CloseError.QueueUnavailable)

# suggested
queue = loaded.unwrap(err=CloseError.QueueUnavailable)
```

`X.unwrap(err=NewErr)` is `X.wrap_err(NewErr).unwrap()` in one call: the old
error is not lost, it survives as a note (see docs/result.md#wrap_err). When
the new error must be *computed from* the old one rather than a fixed
replacement, use `X.map_err(fn).unwrap()` instead -- the finding's message
says so.

See docs/result.md#propagation for both idioms.

### TYP005 -- assert stripped under `-O` (info)

```python
# flagged (informational)
assert result.is_ok
value = result.danger_ok   # under `python -O` this silently returns garbage

# good
value = result.unwrap()          # raises UnwrapError on Err
value = result.expect("loaded")  # raises UnwrapError with a message
```

`assert` statements are compiled out entirely under `python -O`; an
`assert result.is_ok` immediately followed by a statement that reads
`result.danger_ok` (or `.danger_err`/`.danger_some`) loses its guard
silently in that mode. Flags an `assert X.is_ok`/`X.is_err`/`X.is_some`
immediately followed, in the same statement list, by any statement that
somewhere contains `X.danger_ok`/`X.danger_err`/`X.danger_some` on the
same subject `X`.

### TYP006 -- catch/catching with no named exception types (info)

```python
# flagged (informational)
result = Result.catch(lambda: json.loads(text))

@catching(on_error=lambda e: IoError.Failed)
def read_file(path: Path) -> str:
    return path.read_text()

# good
result = Result.catch(lambda: json.loads(text), json.JSONDecodeError, on_error=...)

@catching(OSError, on_error=lambda e: IoError.Failed)
def read_file(path: Path) -> str:
    return path.read_text()
```

Flags a call to `Result.catch(fn, ...)` with no positional exception-type
argument beyond `fn`, or a call/decorator use of `catching(...)` with no
positional exception-type argument at all -- in both cases the default
`(Exception,)` is what actually gets caught, silently converting
*every* exception the callable can raise (including genuine programmer
bugs) into an `Err`. `on_error=...` alone does not silence this: naming
the exception types is what narrows the boundary.

### TYP007 -- broad except inside a Result/Option function (info)

```python
# flagged (informational)
def load(path: Path) -> Result[Config, ConfigError]:
    try:
        return Ok(parse(path))
    except Exception as exc:
        return Err(ConfigError.Invalid(str(exc)))

# good
def load(path: Path) -> Result[Config, ConfigError]:
    try:
        return Ok(parse(path))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return Err(ConfigError.Invalid(str(exc)))
```

Flags a bare `except:`, `except Exception:`, or `except BaseException:`
(including one inside a tuple, e.g. `except (OSError, Exception):`) that
is lexically inside a function or method whose return annotation
(unparsed, forward-reference strings included) is `Result[...]`,
`Option[...]`, or a bare `Result`/`Option`. Inside a function that already
communicates failure through its return type, a catch-all `except`
clause silently reclassifies an unrelated programmer bug (a `TypeError`
from a bad call, a `KeyError` from a typo) as a legitimate domain `Err`,
defeating the whole point of returning `Result`/`Option` in the first
place. `except (OSError, ValueError)`-style named tuples are never
flagged, and a catch-all `except Exception` outside any Result/Option
function (e.g. inside a `-> None` function) is never flagged either --
this rule is about the specific mismatch between a typed failure channel
and an untyped one silently absorbing everything into it. `Result.catch`
is the narrower, explicit alternative for the exception-to-`Result`
boundary (see docs/result.md#catch).

## Suppression

A trailing comment on the offending line suppresses that line's
findings:

```python
if r.ok:  # typani: ignore
    ...

if r.ok:  # typani: ignore[TYP002]
    ...
```

The bare form suppresses every rule on that line; the bracketed form
(comma-separated rule ids allowed) suppresses only the named rule(s).

A `# typani: skip-file` comment anywhere in the first 5 lines of a file
skips the whole file.

## API reference

`typani.lint` exposes a small importable API for embedding the checker in
another tool, alongside the CLI.

### `Finding`

```python
Finding(
    rule: str,
    path: str,
    line: int,
    col: int,
    message: str,
    severity: str,
    symref: str,
)
```

One lint hit: a frozen dataclass with the rule id (e.g. `"TYP001"`), the
file path, 1-based line, 0-based column, a human-readable message,
`severity` (`"error"` or `"info"`), and `symref` -- see "JSON schema"
below for its shape.

### `Report`

```python
Report(version: int, files_scanned: int, findings: list[Finding])
```

The result of one `check_tree` run: the envelope `version`
(`JSON_VERSION`, currently `1`), the count of files actually parsed
(`files_scanned`), and the `findings` list. `render_json` renders a
`Report` as the JSON envelope described in "JSON schema" below.

### `check_source`

```python
check_source(source: str, path: str = "<string>") -> list[Finding]
```

Lints one in-memory source string. A syntax error never raises -- it
becomes a single `Finding(rule="TYP000", severity="error", ...)` instead.
Honors `# typani: skip-file` and `# typani: ignore[...]` on the given
source.

### `check_tree`

```python
check_tree(paths: Iterable[Path], *, exclude: Iterable[str] = ()) -> Report
```

Walks each path for `*.py` files (see "`check_tree` walking rules"
above), runs `check_source` on each, and returns a `Report`: the
findings sorted by `(path, line, col)`, plus the number of files
actually parsed. A file that fails to parse (a `TYP000` syntax error)
still counts toward `files_scanned`.

### `check_paths`

```python
check_paths(paths: Iterable[Path], *, exclude: Iterable[str] = ()) -> list[Finding]
```

Backward-compatible wrapper: `check_tree(paths, exclude=exclude).findings`.
Prefer `check_tree` in new code, since it also reports `files_scanned`.

### `is_skip_file`

```python
is_skip_file(source: str) -> bool
```

`True` when a `typani: skip-file` marker appears in the first 5 lines of
*source*.

### `apply_suppressions`

```python
apply_suppressions(source: str, findings: list[Finding]) -> list[Finding]
```

Drops any finding whose source line carries a matching
`# typani: ignore` (or rule-specific `# typani: ignore[TYP00N]`) comment.

### `render_text`

```python
render_text(findings: list[Finding]) -> str
```

Renders findings as `path:line:col: RULE message` lines, error-severity
findings before info-severity ones, each group sorted.

### `render_json`

```python
render_json(report: Report) -> str
```

Renders a `Report` as the versioned JSON envelope (see "JSON schema"
below), preserving the given finding order.

### `build_parser`

```python
build_parser() -> argparse.ArgumentParser
```

Builds the `argparse` parser backing the CLI described in "Usage" above.

### `main`

```python
main(argv: list[str] | None = None) -> int
```

Runs the CLI end to end -- scan, filter, print the report -- and returns
the process exit code (see "Exit codes" above).

## JSON schema

`--json` prints a versioned envelope, not a bare array -- a bare
top-level array cannot tell a run that scanned 200 files and found
nothing apart from a run that matched zero files, and has no version
field for a consumer to check the shape against:

```json
{
  "version": 1,
  "files_scanned": 214,
  "findings": [
    {
      "rule": "TYP002",
      "path": "src/app/queue.py",
      "line": 42,
      "col": 7,
      "message": "'ok' is the payload or None; falsy payloads (0, '', []) will be misread -- test 'is_ok' instead",
      "severity": "error",
      "symref": "src/app/queue.py::Queue.pop"
    }
  ]
}
```

- `version` is the envelope's format version (`JSON_VERSION`, currently
  `1`). See "Format stability" below.
- `files_scanned` is the count of `*.py` files `check_tree` actually
  parsed, independent of `--select`/`--ignore`/`--no-info` filtering
  (those filter `findings` only). A file that fails to parse (`TYP000`)
  still counts. A run that matches zero files prints
  `"files_scanned": 0, "findings": []` and exits `0` -- it is not
  treated as an error -- but logs a WARNING to stderr:
  `typani.lint: no Python files matched <paths>`, so a silent
  zero-match is loud even though it is not a failure.
- `findings` is the array of finding dicts, in the order described
  under "Text output" above. `severity` is `"error"` or `"info"`. A
  syntax error in a scanned file produces one `TYP000`/`"error"`
  finding for that file instead of raising.
- `symref` binds a finding to a symbol as `"<path>::<qualname>"`, where
  `qualname` is the dotted enclosing scope at the point of the finding:
  a bare class/function name at module scope, `Class.method` inside a
  method, and `outer.inner` for a nested function. Module-level findings
  (not inside any `def`/`class`) get the bare path with no `::`. `TYP000`
  syntax-error findings always get the bare path, since no AST exists to
  derive a scope from.

### Format stability

`version` increments only on a breaking change to the envelope shape or
to an existing finding field's name, type, or order. Adding a new
field -- to the envelope or to a finding -- is never a breaking change
and never bumps `version`. A consumer that receives an unrecognized
`version` should reject the payload loudly (raise, fail the check) rather
than guess at the shape.

## CI recipe

```yaml
- name: typani.lint
  run: python -m typani.lint src tests --no-info
```

Drop `--no-info` to also print (but not fail on) TYP004/TYP005 hits; add
`--json` and pipe to a report step if the CI system wants structured
output instead.

### Field results as an exception-boundary worklist

Run with `--json`, `TYP007`'s findings are a ready-made worklist for a
consumer auditing its own exception boundaries: each finding's `symref`
names the exact function to narrow, and its `message` already states
which broad except clause is the problem. A consumer can filter the
JSON envelope's `findings` array to `rule == "TYP007"` and drive a
migration ticket queue straight from that, without re-deriving the list
by hand.

## Field results

`typani.lint` was run against `frob` (version `0.530.0`, 649 `*.py` files
under `src/`) as a real-world false-positive/true-positive check --
`frob` uses typani's `Result`/`Option` types extensively but was not
written with this checker in mind.

`--no-info` (errors only): 4 findings, all TYP003, all confirmed true
positives by inspection -- each is a bare-statement call to a function
genuinely annotated to return a `Result`:

| File | Line | Rule | Discarded call |
|------|------|------|-----------------|
| `frob/gates/_coverage.py` | 1083 | TYP003 | `write_coverage_lock(...)` (`-> Result[Unit, GateError]`) | <!-- frob:waive DOC006 reason="paths cite the frob repository (../frob), not tracked files here; the field-results table is measured on frob 0.530.0" -->
| `frob/serve/_daemon.py` | 554 | TYP003 | `_poll_verify_worker(...)` (`-> Result[WorkerOutcome, WorkerError] \| None`) |
| `frob/tickets/_land.py` | 2216 | TYP003 | `_land_plan_unwind_after_merge(...)` (`-> Result[None, LandError]`) |
| `frob/tickets/_land.py` | 6959 | TYP003 | `_check_tdd_order(...)` (`-> Result[None, LandError]`) |

With info-severity findings included: TYP004 (propagation boilerplate)
fired 649 times -- close to `docs/redesign-0.1.md` section 1.1's
independent grep-based estimate of 651 `if x.is_err: return
Err(x.danger_err)`-shaped blocks, corroborating that the AST rule
captures the same real pattern the manual audit found. TYP005 fired 0
times (that shape is rarer in practice). TYP002 fired 0 times after the
evidence-based tightening described above; the earlier, untightened
version had fired 16 times, all 16 confirmed false positives (see
TYP002's rule section).

### T-0028 field results: TYP004 mapped shape, TYP006, TYP007

Re-run against the same `frob` `src/` tree (649 `*.py` files) after T-0028
added the mapped-error TYP004 shape and the TYP006/TYP007 rules:

- TYP004 fired 676 times total: 649 pass-through (unchanged from the
  earlier measurement above) plus 27 mapped-error hits (`if X.is_err:
  return Err(<mapped>)`).
- TYP006 fired 0 times: every `Result.catch`/`catching` use found already
  named its exception types.
- TYP007 fired 17 times, all `except Exception` inside a `Result`-returning
  function -- well under the ~93-site estimate a manual review of the
  same tree had made; the manual estimate likely counted broad excepts
  reachable from a `Result`-returning function indirectly (through a
  helper) rather than lexically inside one, which this rule deliberately
  does not follow (see TYP007 above). Five example symrefs:
  - `frob/fleet/__init__.py::load_manifest` <!-- frob:waive DOC006 reason="paths cite the frob repository (../frob), not tracked files here; measured on frob 0.530.0" -->
  - `frob/fuzz/_arbitrary.py::_field_strategy` <!-- frob:waive DOC006 reason="paths cite the frob repository (../frob), not tracked files here; measured on frob 0.530.0" -->
  - `frob/fuzz/_arbitrary.py::_derived_strategy` <!-- frob:waive DOC006 reason="paths cite the frob repository (../frob), not tracked files here; measured on frob 0.530.0" -->
  - `frob/gates/_coverage.py::load_coverage` <!-- frob:waive DOC006 reason="paths cite the frob repository (../frob), not tracked files here; measured on frob 0.530.0" -->
  - `frob/gates/_ratchet.py::_write_ratchet_lock` <!-- frob:waive DOC006 reason="paths cite the frob repository (../frob), not tracked files here; measured on frob 0.530.0" -->

## frob recipe

As of this writing frob's `[policy]` table (`frob.toml`) supports three
rule kinds -- `forbidden-import`, `pattern` (a tree-sitter query), and
`norm` (a diff-shape rule) -- and has **no command-runner policy kind**
(see `/home/logan/projects/frob/docs/modules/gates.md`, the
`PolicyKind`/`PolicyRule` section: "the three rule kinds `frob.toml`'s
`[policy]` table supports at alpha"). There is therefore no
`[[policy.command]]`-shaped way to wire `python -m typani.lint` into
`frob check` directly today. Run it as a plain CI step (above) in a
frob-enabled repo the same way as anywhere else. If frob later adds a
command-based policy kind, this section should be revisited to wire
`typani.lint` in natively; no `frob:todo` is left for this in
`src/typani/lint` itself since the missing capability lives in frob, a
different project, not in this repo.
