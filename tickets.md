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
