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
