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

<!-- ticket:T-0015 -->
```yaml
id: T-0015
title: 'frob compliance sweep after 0.1: DOC004/DOC006/DOC011 anchors, REF entrypoints,
  strata nodes for bench/crates/scripts/tests, capability ratchet'
state: queued
kind: feature
origin: agent
created: '2026-09-05'
priority: high
parent: T-0007
tier: ticket
sprint: null
runs_last: false
milestone: null
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- README.md
- docs/*.md
- frob.toml
- design/typani.strata
- docs/design/registry/*
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
Drive frob check from 63 errors to zero. DOC004: bind every doc code block with a frob:describes anchor. DOC006/DOC011: waive external frob paths and frob ticket ids cited in docs/lint.md and docs/redesign-0.1.md with reasons. REF001/REF002: [[refs.entrypoint]] declarations for build/tool files and second references where a doc is genuinely linked once. SELFAUDIT SYS103/SYS111: strata nodes with declared may capabilities for bench/, crates/typani-core/, scripts/, tests/, and raise the capability-via ratchet ceilings for impl_mod env.read and lint fs-read.
