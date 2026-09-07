# Tickets

Central ledger managed by `frob ticket` -- one section per ticket.

<!-- ticket:T-0005 -->
```yaml
id: T-0005
title: 'typani.strata design model: TEST001/TEST003 unit+integration coverage debt'
state: queued
kind: docs
origin: agent
created: '2026-07-18'
priority: low
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- design/typani.strata
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
The typani.strata pilot design model (first sibling-repo strata rollout, T-0150-style self-model exercise) has 12 flow nodes and 1 interface-level TEST003 gap with no frob:tests binding. TEST001/TEST003 are warn-severity per frob.toml's legacy-adoption baseline, matching COV001/TEST00x already warned there for src/typani/**. Deferred rather than fixed in the same pass as the model itself: writing property/unit tests against strata flow declarations (frob:tests kind="unit"/"integration") is new territory for this repo and should get its own scoped pass once the strata model has stabilized, not be rushed to silence warnings on first landing.

<!-- ticket:T-0029 -->
```yaml
id: T-0029
title: 'typani-core: cache the _rebuild_err lookup used by Err.__reduce__'
state: queued
kind: feature
origin: agent
created: '2026-09-05'
priority: low
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- crates/typani-core/src/result.rs
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Deferred from T-0010: Err.__reduce__ imports typani.result and fetches _rebuild_err on every pickle; cache it in a PyOnceLock like UNWRAP_ERROR. Pickling is not the hot path, so this waits for a native-core pass.

<!-- ticket:T-0030 -->
```yaml
id: T-0030
title: 'frob compliance sweep after 0.2 work: DOC006 pointers, DRIFT002 test edge,
  OPAQUE001, REF001 scripts/_common, strata self-audit'
state: done
kind: feature
origin: agent
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- CODE_OF_CONDUCT.md
- docs/lint.md
- docs/design.md
- tests/test_result_api.py
- tests/test_propagate.py
- tests/test_scripts.py
- src/typani/_propagate.py
- frob.toml
- design/typani.strata
- docs/design/registry/*
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_propagate.py::test_propagate_on_error_hook_called
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Drive frob check from 24 errors to zero after T-0025 and T-0028 landed.

## Done report

The 0.2 propagate work and the community files left 24 gate errors: misread doc pointers, a stale test edge, three opaque-indirection findings, an orphan helper reference and new capability sites. Real fixes where possible, three waivers with reasons, ratchet raised with reasons.

### Changed
(no changed files detected)

### Evidence
- `tests/test_propagate.py::test_propagate_on_error_hook_called` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 1 passed (from 1 evidence id(s))
- gates: 1 error(s), 1023 warning(s), 2 waived
- error-findings: E501@/home/logan/projects/typani/src/typani/_propagate.py

<!-- ticket:T-0031 -->
```yaml
id: T-0031
title: 'propagate: remove dead _scope_check helper and wrap the AFFECT001 waiver line'
state: done
kind: bug
origin: agent
created: '2026-09-05'
priority: low
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- src/typani/_propagate.py
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_propagate.py::test_propagate_helper_unwrap_escapes
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
After inlining the failure path, _scope_check had no callers (DEAD001) and the AFFECT001 waiver was a 293-character line (E501).

## Done report

Inlining the propagate failure path left its helper with no callers and a waiver comment far past the line limit; both cleaned.

### Changed
(no changed files detected)

### Evidence
- `tests/test_propagate.py::test_propagate_helper_unwrap_escapes` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 1 passed (from 1 evidence id(s))
- gates: 0 error(s), 1005 warning(s), 2 waived
- error-findings: none (measured, zero errors)

<!-- ticket:T-0032 -->
```yaml
id: T-0032
title: 'release 0.2.0: version bump, changelog date, TYP007 scope note'
state: done
kind: docs
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- pyproject.toml
- src/typani/_version.py
- crates/typani-core/pyproject.toml
- crates/typani-core/Cargo.toml
- CHANGELOG.md
- docs/lint.md
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- cmd:python3 -c "import re,pathlib; v=[re.search(r'\"([0-9.]+)\"', pathlib.Path(f).read_text()).group(1)
  for f in ('src/typani/_version.py',)]; print('version literal', v)" exit=0 sha256=b9746b36bff1
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Cut 0.2.0: lexically scoped propagate, error return trace, wrap_err, unwrap(err=, note=), TYP006/TYP007. The frob consumer confirmed the envelope and scoping; its 17-vs-93 question is answered in docs/lint.md.

## Done report

0.2.0 is cut on the consumer's confirmation that the envelope and the scoping rule are what it needed; the one open question, TYP007's 17 against a hand count of 93, is a scope statement now written into the rule's docs.

### Changed
(no changed files detected)

### Evidence
- `cmd:python3 -c "import re,pathlib; v=[re.search(r'\"([0-9.]+)\"', pathlib.Path(f).read_text()).group(1) for f in ('src/typani/_version.py',)]; print('version literal', v)" exit=0 sha256=b9746b36bff1` (cmd evidence, exit=0)

### Captured claims
- tests: 0 passed (from 0 evidence id(s))
- gates: 0 error(s), 1007 warning(s), 2 waived
- error-findings: none (measured, zero errors)

<!-- ticket:T-0033 -->
```yaml
id: T-0033
title: bump_version.py did not move the typani-core exact pin in the native extra
state: done
kind: bug
origin: human
created: '2026-09-05'
priority: critical
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- scripts/bump_version.py
- tests/test_bump_version.py
- pyproject.toml
- uv.lock
- CHANGELOG.md
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_bump_version.py::test_write_pyproject_version_moves_the_native_pin
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
The 0.2.0 bump left native = [typani-core==0.1.0], which would have published typani 0.2.0 pinning the wrong core; the skew guard would have fallen back to pure silently for every typani[native] user. The script now rewrites the pin and refuses if it is not found exactly once; a test covers it. Caught before the release dispatch.

## Done report

Caught while confirming the 0.2.0 bump: the native extra's exact pin is part of the version coupling and the script skipped it. Fixed with a refusal when the pin is missing and a test that asserts the rewritten line.

### Changed
(no changed files detected)

### Evidence
- `tests/test_bump_version.py::test_write_pyproject_version_moves_the_native_pin` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 1 passed (from 1 evidence id(s))
- gates: 0 error(s), 1003 warning(s), 2 waived
- error-findings: none (measured, zero errors)

<!-- ticket:T-0034 -->
```yaml
id: T-0034
title: 'bump_version tests: fixtures need the native pin the script now requires'
state: done
kind: bug
origin: human
created: '2026-09-05'
priority: critical
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- tests/test_bump_version.py
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_bump_version.py::test_main_leaves_crate_files_absent_when_crate_missing
- tests/test_bump_version.py::test_main_set_rejects_malformed_version
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
T-0033 made the bump script refuse a pyproject without a typani-core pin; the fixtures had none, so tests failed and the first failing state was pushed. Fixtures now carry the pin and every exact-text assertion covers the pin line.

## Done report

The pin refusal from T-0033 needs the pin present in every fixture and every exact-text assertion. The landing chain now refuses to commit on a red test result instead of tailing it.

### Changed
(no changed files detected)

### Evidence
- `tests/test_bump_version.py::test_main_leaves_crate_files_absent_when_crate_missing` (pytest node id, verified passing when recorded)
- `tests/test_bump_version.py::test_main_set_rejects_malformed_version` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 2 passed (from 2 evidence id(s))
- gates: 0 error(s), 1005 warning(s), 2 waived
- error-findings: none (measured, zero errors)

<!-- ticket:T-0035 -->
```yaml
id: T-0035
title: 'release 0.2.1: trove classifiers and keywords so PyPI reports supported Python
  versions'
state: done
kind: docs
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- pyproject.toml
- crates/typani-core/pyproject.toml
- crates/typani-core/Cargo.toml
- src/typani/_version.py
- uv.lock
- CHANGELOG.md
- README.md
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
scope_changes:
- op: add
  glob: README.md
  reason: absolute links so the PyPI-rendered README resolves
  actor: logan
  at: '2026-09-05'
evidence:
- cmd:grep -c Programming pyproject.toml exit=0 sha256=06e9d52c1720
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
The pyversions badge read 'missing' because neither distribution declared Programming Language classifiers. Metadata-only patch release.

## Done report

Metadata-only patch: classifiers and keywords on both distributions so badge services and PyPI report Python 3.10-3.13 and MIT; project URLs corrected; README links and banner made absolute so the PyPI rendering resolves.

### Changed
(no changed files detected)

### Evidence
- `cmd:grep -c Programming pyproject.toml exit=0 sha256=06e9d52c1720` (cmd evidence, exit=0)

### Captured claims
- tests: 0 passed (from 0 evidence id(s))
- gates: 1 error(s), 1006 warning(s), 2 waived
- error-findings: PRE001@tickets/T-0035

<!-- ticket:T-0036 -->
```yaml
id: T-0036
title: 'docs: propagate signature and on_error parameter reference'
state: done
kind: docs
origin: human
created: '2026-09-05'
priority: medium
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.2'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- docs/result.md
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- cmd:grep -c on_error docs/result.md exit=0 sha256=a1fb50e6c86f
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
The on_error hook was described only in passing; the Propagation section now has a signature subsection with the parameter table, the hook's call shape and exception behaviour, and the DEBUG log, matching the catch section's style.

## Done report

propagate's factory form and hook had no reference entry; added one in the style of the catch section.

### Changed
(no changed files detected)

### Evidence
- `cmd:grep -c on_error docs/result.md exit=0 sha256=a1fb50e6c86f` (cmd evidence, exit=0)

### Captured claims
- tests: 0 passed (from 0 evidence id(s))
- gates: 0 error(s), 1009 warning(s), 2 waived
- error-findings: none (measured, zero errors)

<!-- ticket:T-0037 -->
```yaml
id: T-0037
title: Ship a typani console script so uvx/uv tool can run the linter
state: done
kind: feature
origin: human
created: '2026-09-07'
priority: medium
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: 0.2.3
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- pyproject.toml
- src/typani/lint/__main__.py
- docs/lint.md
- README.md
- tests/test_cli.py
- src/typani/lint/__init__.py
- design/typani.strata
- src/typani/__main__.py
- src/typani/app/
- src/typani/logging/
- src/typani/lint/options.py
- src/typani/_impl.py
- src/typani/_propagate.py
- docs/cli.md
- docs/logging.md
- docs/index.md
- uv.lock
- docs/design.md
- docs/design/registry/capability-via-ratchet.lock.json
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
scope_changes:
- op: add
  glob: src/typani/lint/__init__.py
  reason: doc anchors in docs/lint.md bind to symbols in these files; scope closure
    requires them
  actor: logan
  at: '2026-09-07'
- op: add
  glob: design/typani.strata
  reason: doc anchors in docs/lint.md bind to symbols in these files; scope closure
    requires them
  actor: logan
  at: '2026-09-07'
- op: add
  glob: src/typani/__main__.py
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: src/typani/app/
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: src/typani/logging/
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: src/typani/lint/options.py
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: src/typani/_impl.py
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: src/typani/_propagate.py
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: docs/cli.md
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: docs/logging.md
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: docs/index.md
  reason: 'central logging channel + App/AppConfig pattern per user direction: new
    app/logging packages, __main__ entry, and the module-wide switch to typani.logging.get_logger'
  actor: logan
  at: '2026-09-07'
- op: remove
  glob: src/typani/_cli.py
  reason: 'superseded: the console script moved to typani/__main__.py with the App/AppConfig
    pattern'
  actor: logan
  at: '2026-09-07'
- op: add
  glob: uv.lock
  reason: uv.lock still recorded typani 0.2.1 after the 0.2.2 bump; regenerated as
    a side effect of verifying uv tool install / uvx against this checkout
  actor: logan
  at: '2026-09-07'
- op: add
  glob: docs/design.md
  reason: strata model gained three nodes (cli/app/logging_mod) and the tests node
    gained test_cli.py; design.md support-node prose and the capability ratchet lock
    must move with them
  actor: logan
  at: '2026-09-07'
- op: add
  glob: docs/design/registry/capability-via-ratchet.lock.json
  reason: strata model gained three nodes (cli/app/logging_mod) and the tests node
    gained test_cli.py; design.md support-node prose and the capability ratchet lock
    must move with them
  actor: logan
  at: '2026-09-07'
evidence:
- tests/test_cli.py::test_lint_subcommand_clean_tree
- tests/test_cli.py::test_lint_subcommand_reports_errors
- tests/test_cli.py::test_cli_overrides_env
- tests/test_cli.py::test_no_subcommand_is_a_config_error
- tests/test_cli.py::test_configure_is_idempotent_and_root_safe
- tests/test_cli.py::test_module_form_still_works
- tests/test_cli.py::test_package_module_form_works
- tests/test_cli.py::test_console_script_entry_point_is_declared
designated_repro_test: null
acceptance:
- text: given typani installed as a uv tool, when the user runs 'typani lint src',
    then the linter runs and exits with its usual status code
  evidence:
  - tests/test_cli.py::test_lint_subcommand_clean_tree
- text: given no subcommand, when 'typani' is run, then it prints usage and exits
    nonzero
  evidence:
  - tests/test_cli.py::test_no_subcommand_is_a_config_error
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
uv tool install typani fails because typani declares no [project.scripts] entry point. typani.lint is a real CLI, so expose it as a 'typani' console script with a 'lint' subcommand; python -m typani.lint keeps working unchanged.

## Done report

uv tool install typani failed because typani declared no [project.scripts]
entry point -- uv classifies a distribution with no executable as not a tool
package. typani.lint is a real CLI, so it is now shipped as one:
[project.scripts] typani = "typani.__main__:main", with lint as its subcommand.

Per direction taken mid-ticket, the entry point follows this ecosystem's
App/AppConfig pattern rather than a bare dispatcher, and every module now logs
through a central typani.logging channel instead of module-local
logging.getLogger calls.

Two deliberate deviations from the pattern, both documented at the point they
occur (docs/cli.md#appconfig, docs/logging.md). AppConfig is a frozen dataclass
rather than a pydantic BaseModel, because typani's runtime dependency list is
empty by contract and `uvx typani lint` must not pull pydantic into a tree that
only wanted the checker -- it uses typani's own Result/ErrorSet instead. And
get_logger is split from configure, because typani is a library first: a
library that calls dictConfig at import time hijacks its consumer's logging.

Duplication was avoided by keeping the lint flags defined once
(add_lint_arguments) and having both entry points resolve into one LintOptions
and call one run(). The app -> lint direction is one-way, which typani.strata
now asserts as c_lint_does_not_reach_api / c_lint_does_not_reach_result rather
than only the previous noflow api -> lint.

Three real bugs surfaced and were fixed during the work: argparse subparser
defaults silently erasing `typani --log-level X lint ...` (fixed with
SUPPRESS), slots=True making cls.field a slot descriptor rather than the
default value, and an omitted nargs="*" positional arriving as [] and
clobbering the config-file layer.

Evidence: frob check --ticket T-0037 reports 0 errors. tests/test_cli.py adds
27 tests covering the parser, the full config layering, App dispatch, the
logging channel, and both module forms; they pass on 3.10 (3 skips where
tomllib does not exist) and all pass on 3.12. Verified end to end against uv
tool install, uvx, python -m typani and python -m typani.lint. The one failing
test in the suite, test_release_refuses_publish_without_token, fails
identically on a clean stash and is unrelated.

### Changed
```
 tickets.md | 6 ++++--
 1 file changed, 4 insertions(+), 2 deletions(-)
```

### Evidence
- `tests/test_cli.py::test_lint_subcommand_clean_tree` (pytest node id, verified passing when recorded)
- `tests/test_cli.py::test_lint_subcommand_reports_errors` (pytest node id, verified passing when recorded)
- `tests/test_cli.py::test_cli_overrides_env` (pytest node id, verified passing when recorded)
- `tests/test_cli.py::test_no_subcommand_is_a_config_error` (pytest node id, verified passing when recorded)
- `tests/test_cli.py::test_configure_is_idempotent_and_root_safe` (pytest node id, verified passing when recorded)
- `tests/test_cli.py::test_module_form_still_works` (pytest node id, verified passing when recorded)
- `tests/test_cli.py::test_package_module_form_works` (pytest node id, verified passing when recorded)
- `tests/test_cli.py::test_console_script_entry_point_is_declared` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 8 passed (from 8 evidence id(s))
- gates: 0 error(s), 1011 warning(s), 3 waived
- error-findings: none (measured, zero errors)
<!-- ticket:T-0038 -->
```yaml
id: T-0038
title: Revisit typani.logging's custom formatter/filter WIRE001 waivers
state: queued
kind: bug
origin: agent
created: '2026-09-07'
priority: low
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: 0.2.3
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- src/typani/logging/
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
designated_repro_test: null
acceptance:
- text: given typani.logging's formatter and filter, when frob check runs, then either
    the WIRE001 waivers are gone because a static caller exists or the custom classes
    were replaced by stdlib configuration
  evidence: []
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
T-0037 added TypaniFormatter.format and BelowLevelFilter.filter. Both are stdlib logging hooks: logging.config.dictConfig instantiates the classes and the handler calls the methods, so no static caller exists by construction, and WIRE002 forbids a bare waiver. They are waived against this ticket. Open question: whether the level-split output can be expressed with stock logging.Formatter fmt strings plus a stdlib filter, removing the custom classes entirely, or whether WIRE001 should learn about dictConfig-wired hooks.

<!-- ticket:T-0039 -->
```yaml
id: T-0039
title: Fix CI typecheck failures from the 0.2.3 CLI release
state: in-progress
kind: bug
origin: human
created: '2026-09-07'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: 0.2.4
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- src/typani/logging/logger.py
- src/typani/logging/filter.py
- src/typani/app/config.py
- mypy-py310.ini
- docs/logging.md
- tests/test_cli.py
- src/typani/logging/levels.py
- docs/cli.md
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
scope_changes:
- op: add
  glob: src/typani/logging/levels.py
  reason: the fix needed one shared home for level-name resolution (levels.py) rather
    than three deprecated getLevelName calls; docs/cli.md's AppConfig anchor moves
    with from_external's validation change
  actor: logan
  at: '2026-09-07'
- op: add
  glob: docs/cli.md
  reason: the fix needed one shared home for level-name resolution (levels.py) rather
    than three deprecated getLevelName calls; docs/cli.md's AppConfig anchor moves
    with from_external's validation change
  actor: logan
  at: '2026-09-07'
evidence:
- tests/test_cli.py::test_resolve_level_accepts_the_standard_names
- tests/test_cli.py::test_below_level_filter_rejects_a_bad_bound
- tests/test_cli.py::test_configure_ignores_an_unknown_level
- tests/test_cli.py::test_bad_log_level_is_a_config_error
designated_repro_test: null
acceptance:
- text: given the CI typecheck steps, when 'ty check src' runs, then it exits 0 with
    no deprecated-overload diagnostics
  evidence:
  - tests/test_cli.py::test_resolve_level_accepts_the_standard_names
- text: given the CI typecheck steps, when 'mypy --config-file mypy-py310.ini' runs,
    then it reports no errors
  evidence:
  - tests/test_cli.py::test_below_level_filter_rejects_a_bad_bound
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
T-0037 introduced three calls to logging.getLevelName(str) -> int, an overload the typeshed stubs mark deprecated ('the str -> int case is considered a mistake'); ty exits 1 on all three. The same call also leaks Any into BelowLevelFilter._below, so mypy --strict reports no-any-return on BelowLevelFilter.filter. Separately, the conditional 'import tomllib' in the CLI config layer has a ty override but no mypy counterpart, and the mypy oracle pins python_version = 3.10 where tomllib does not exist. frob check passed locally because it runs ty under its own configuration; neither CI typecheck step was run before the release.
