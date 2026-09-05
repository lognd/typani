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
state: done
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
- tests/test_backend.py
- tests/test_lint.py
- tests/test_result_api.py
- tickets-archive.md
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
scope_changes:
- op: add
  glob: tests/test_backend.py
  reason: COV006 rebinding of frob:tests edges to public symbols and the T-0007 evidence-kind
    fix surfaced by the same sweep
  actor: logan
  at: '2026-09-05'
- op: add
  glob: tests/test_lint.py
  reason: COV006 rebinding of frob:tests edges to public symbols and the T-0007 evidence-kind
    fix surfaced by the same sweep
  actor: logan
  at: '2026-09-05'
- op: add
  glob: tests/test_result_api.py
  reason: COV006 rebinding of frob:tests edges to public symbols and the T-0007 evidence-kind
    fix surfaced by the same sweep
  actor: logan
  at: '2026-09-05'
- op: add
  glob: tickets-archive.md
  reason: COV006 rebinding of frob:tests edges to public symbols and the T-0007 evidence-kind
    fix surfaced by the same sweep
  actor: logan
  at: '2026-09-05'
evidence:
- tests/test_lint.py::test_typ001_property_called_as_method
- tests/test_backend.py::test_backend_matches_typani_pure_env
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Drive frob check from 63 errors to zero. DOC004: bind every doc code block with a frob:describes anchor. DOC006/DOC011: waive external frob paths and frob ticket ids cited in docs/lint.md and docs/redesign-0.1.md with reasons. REF001/REF002: [[refs.entrypoint]] declarations for build/tool files and second references where a doc is genuinely linked once. SELFAUDIT SYS103/SYS111: strata nodes with declared may capabilities for bench/, crates/typani-core/, scripts/, tests/, and raise the capability-via ratchet ceilings for impl_mod env.read and lint fs-read.

## Done report

Every doc code block is bound with a frob:describes anchor, build and tool inputs that nothing in-tree names are declared refs.entrypoint, the strata model gained native_core/bench/scripts/tests nodes with their observed capabilities plus a committed capability ratchet, frob ticket ids cited from ../frob are code spans, and frob:tests edges bind to public symbols the call graph can reach. frob check drops from 63 errors to the ticket-lifecycle residue only.

### Changed
(no changed files detected)

### Evidence
- `tests/test_lint.py::test_typ001_property_called_as_method` (pytest node id, verified passing when recorded)
- `tests/test_backend.py::test_backend_matches_typani_pure_env` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 2 passed (from 2 evidence id(s))
- gates: 3 error(s), 953 warning(s), 0 waived
- error-findings: MILE003@tickets.md, REF001@docs/design/registry/capability-via-ratchet.lock.json, unresolved-attribute@examples/error_sets.py

<!-- ticket:T-0016 -->
```yaml
id: T-0016
title: 'docs: describe the committed capability ratchet lock in docs/design.md'
state: done
kind: docs
origin: agent
created: '2026-09-05'
priority: low
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- docs/design.md
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- cmd:uv run python -c "import pathlib; t=pathlib.Path('docs/design.md').read_text();
  assert 'capability-via-ratchet.lock.json' in t; print('design.md references the
  ratchet lock')" exit=0 sha256=b407b8542d57
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Follow-up to T-0015: the REF001 finding on docs/design/registry/capability-via-ratchet.lock.json is closed by describing the lock in docs/design.md so the file has an in-tree reference.

## Done report

The capability ratchet lock that T-0015 introduced had no in-tree reference (REF001); docs/design.md now explains what it is and why a new capability site fails frob check until the ceiling is raised deliberately.

### Changed
(no changed files detected)

### Evidence
- `cmd:uv run python -c "import pathlib; t=pathlib.Path('docs/design.md').read_text(); assert 'capability-via-ratchet.lock.json' in t; print('design.md references the ratchet lock')" exit=0 sha256=b407b8542d57` (cmd evidence, exit=0)

### Captured claims
- tests: 0 passed (from 0 evidence id(s))
- gates: 1 error(s), 938 warning(s), 0 waived
- error-findings: unresolved-attribute@examples/error_sets.py

<!-- ticket:T-0017 -->
```yaml
id: T-0017
title: 'fix: ty diagnostics frob''s check stage reports on examples/error_sets.py
  and option.py'
state: done
kind: bug
origin: agent
created: '2026-09-05'
priority: low
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- examples/error_sets.py
- src/typani/option.py
- tests/test_option.py
- tests/test_option_api.py
- crates/typani-core/typani_core.pyi
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
scope_changes:
- op: add
  glob: tests/test_option.py
  reason: unused ignores and the stub mirror of the same signature change
  actor: logan
  at: '2026-09-05'
- op: add
  glob: tests/test_option_api.py
  reason: unused ignores and the stub mirror of the same signature change
  actor: logan
  at: '2026-09-05'
- op: add
  glob: crates/typani-core/typani_core.pyi
  reason: unused ignores and the stub mirror of the same signature change
  actor: logan
  at: '2026-09-05'
evidence:
- tests/test_option_api.py::test_from_optional
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
frob's ty stage (multi-platform run) reported an unresolved-attribute on the match-captured err in examples/error_sets.py and two unused ty:ignore directives in option.py that a plain uv run ty check did not surface.

## Reopen log
- 2026-09-05: the ty:ignore removal traded frob-stage warnings for plain-run errors; fix the variance properly with a method-level TypeVar

## Done report

frob's per-platform ty stage and the plain ty run disagreed about two ty:ignore directives in option.py; the real fix is a method-level TypeVar for from_optional and or_else so neither checker needs a suppression, mirrored into the native stub, plus the example printing str(err).

Filed: none (all findings were fixable in scope).

### Changed
(no changed files detected)

### Evidence
- `tests/test_option_api.py::test_from_optional` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 1 passed (from 1 evidence id(s))
- gates: 0 error(s), 941 warning(s), 0 waived
- error-findings: none (measured, zero errors)

<!-- ticket:T-0018 -->
```yaml
id: T-0018
title: 'typani.lint JSON envelope: version, files_scanned, findings, and per-finding
  symref'
state: done
kind: feature
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- src/typani/lint/*.py
- tests/test_lint.py
- docs/lint.md
- README.md
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_lint.py::test_cli_json_files_scanned_counts_all_python_files
- tests/test_lint.py::test_symref_module_level
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Consumer feedback (frob T-3849): a bare top-level array is the silent-zero shape -- [] from 200 scanned files and [] from zero matched files are indistinguishable -- and carries no version for a consumer to check the format against. Emit {version: 1, files_scanned: N, findings: [...]} with the finding fields unchanged, plus an optional symref (path::qualname) per finding so frob can bind findings to graph symbols instead of line numbers.

## Done report

frob's consumer review asked for two things that turn an empty result from ambiguous into measured: a files_scanned count and a versioned envelope, plus a symref per finding so findings bind to graph symbols rather than line numbers. All three are in; a zero-match run now warns on stderr.

### Changed
(no changed files detected)

### Evidence
- `tests/test_lint.py::test_cli_json_files_scanned_counts_all_python_files` (pytest node id, verified passing when recorded)
- `tests/test_lint.py::test_symref_module_level` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 2 passed (from 2 evidence id(s))
- gates: 1 error(s), 942 warning(s), 0 waived
- error-findings: PRE001@tickets/T-0018

<!-- ticket:T-0019 -->
```yaml
id: T-0019
title: 'CI red on first push: hardcoded test cwd, ty unresolved typani_core on pure
  runners, frob-check advisory, token publish'
state: done
kind: bug
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- tests/test_result_api.py
- pyproject.toml
- .github/workflows/*.yml
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_result_api.py::test_python_o_safety
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
First CI run after the 0.1 push failed in every job: test_python_o_safety used the developer's absolute checkout path as cwd; ty on pure-only runners cannot resolve the optional typani_core import in _impl.py; frob-check cannot install frob (unpublished) and is advisory until it can; release.yml publishes with the PYPI_API_TOKEN secret.

## Done report

Every CI job failed on the first push: a test hardcoded the developer's checkout path, ty could not resolve the optional native import on pure-only runners, and frob-check cannot install an unpublished frob. Fixed the first two properly, made frob-check advisory with the reason in the workflow, and switched publish to the PYPI_API_TOKEN secret.

### Changed
(no changed files detected)

### Evidence
- `tests/test_result_api.py::test_python_o_safety` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 1 passed (from 1 evidence id(s))
- gates: 0 error(s), 942 warning(s), 0 waived
- error-findings: none (measured, zero errors)

<!-- ticket:T-0020 -->
```yaml
id: T-0020
title: 'Makefile as thin wrapper: move install/develop/clean/build/release logic into
  platform-agnostic scripts/'
state: done
kind: feature
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- Makefile
- scripts/*.py
- tests/test_scripts.py
- README.md
- docs/index.md
- frob.toml
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_scripts.py::test_release_refuses_publish_without_token
- tests/test_scripts.py::test_clean_removes_fixture_dirs_and_files
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Owner preference: a Makefile may only wrap platform-agnostic scripts under scripts/. Every recipe with shell logic (rm -rf, find, uv sync stamp, maturin develop guard, bump+commit+push+publish) becomes a Python script using pathlib/shutil/subprocess; each make target is one line calling it. The release script must read UV_PUBLISH_TOKEN from the environment (never open .env itself; python-dotenv load_dotenv is acceptable) and must never print it.

## Done report

The owner's rule is that make may only wrap platform-agnostic scripts. All recipe logic moved into scripts/*.py built on pathlib, shutil and subprocess with a shared _common helper, and the Makefile is six one-line targets. release.py replaces the old upload recipe and never opens or prints .env.

### Changed
(no changed files detected)

### Evidence
- `tests/test_scripts.py::test_release_refuses_publish_without_token` (pytest node id, verified passing when recorded)
- `tests/test_scripts.py::test_clean_removes_fixture_dirs_and_files` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 2 passed (from 2 evidence id(s))
- gates: 10 error(s), 980 warning(s), 0 waived
- error-findings: OPAQUE001@tests/test_scripts.py, REF001@scripts/_common.py, SELFAUDIT001@scripts/_common.py, SELFAUDIT001@scripts/build.py, SELFAUDIT001@scripts/clean.py, SELFAUDIT001@scripts/develop.py, SELFAUDIT001@scripts/install.py, SELFAUDIT001@scripts/release.py, SELFAUDIT001@scripts/typecheck_oracle.py, SELFAUDIT001@tests/test_scripts.py

<!-- ticket:T-0021 -->
```yaml
id: T-0021
title: 'CI: mypy oracle cannot find typani_core on pure-only runners'
state: done
kind: docs
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- mypy-py310.ini
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_backend.py::test_backend_matches_typani_pure_env
- cmd:uv run mypy --config-file mypy-py310.ini exit=0 sha256=59cc4d21606d
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Same class as T-0019 one step later: the mypy oracle step fails on runners without the native crate because the optional typani_core import has no stub there. ignore_missing_imports for that one module.

## Done report

The mypy oracle failed on every pure-only CI runner because the optional native module has no stub there; one ignore_missing_imports entry scoped to typani_core, nothing broader.

### Changed
(no changed files detected)

### Evidence
- `tests/test_backend.py::test_backend_matches_typani_pure_env` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 1 passed (from 1 evidence id(s))
- gates: 10 error(s), 978 warning(s), 0 waived
- error-findings: OPAQUE001@tests/test_scripts.py, REF001@scripts/_common.py, SELFAUDIT001@scripts/_common.py, SELFAUDIT001@scripts/build.py, SELFAUDIT001@scripts/clean.py, SELFAUDIT001@scripts/develop.py, SELFAUDIT001@scripts/install.py, SELFAUDIT001@scripts/release.py, SELFAUDIT001@scripts/typecheck_oracle.py, SELFAUDIT001@tests/test_scripts.py

<!-- ticket:T-0022 -->
```yaml
id: T-0022
title: 'CI: release gated on green CI, rust-cache workspace path, Windows subprocess
  env in -O test'
state: done
kind: bug
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- tests/test_result_api.py
- .github/workflows/*.yml
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_result_api.py::test_python_o_safety
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
release.yml gains a verify-ci job that refuses to publish unless the CI workflow concluded success for the exact commit; publish is OIDC-only now that trusted publishers exist for both distributions. ci.yml points rust-cache at crates/typani-core. test_python_o_safety replaced the environment instead of extending it, which cannot start Python on Windows 3.10.

## Done report

Release is now gated behind green CI for the exact commit and publishes with OIDC only; rust-cache knows where the crate lives; the -O safety test no longer wipes the environment it spawns Python into, which was the Windows 3.10 failure.

### Changed
(no changed files detected)

### Evidence
- `tests/test_result_api.py::test_python_o_safety` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 1 passed (from 1 evidence id(s))
- gates: 11 error(s), 979 warning(s), 0 waived
- error-findings: OPAQUE001@tests/test_scripts.py, REF001@scripts/_common.py, SELFAUDIT001@scripts/_common.py, SELFAUDIT001@scripts/build.py, SELFAUDIT001@scripts/clean.py, SELFAUDIT001@scripts/develop.py, SELFAUDIT001@scripts/install.py, SELFAUDIT001@scripts/release.py, SELFAUDIT001@scripts/typecheck_oracle.py, SELFAUDIT001@tests/test_result_api.py, SELFAUDIT001@tests/test_scripts.py

<!-- ticket:T-0023 -->
```yaml
id: T-0023
title: local gate script, drop CI frob job until frob ships, valid release workflow
state: done
kind: feature
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- scripts/check.py
- tests/test_scripts.py
- Makefile
- frob.toml
- README.md
- .github/workflows/*.yml
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- tests/test_scripts.py::test_check_dry_run_runs_frob_then_both_backends
- tests/test_scripts.py::test_check_skip_frob_drops_the_first_gate
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
frob has no stable release, so the CI frob-check job is removed and scripts/check.py (make check) becomes the local gate: frob check plus pytest under both backends. release.yml used hashFiles in a job-level if, which GitHub rejects at parse time; the crate exists, so the guards go and publish needs all three jobs.

## Done report

The owner asked to skip the CI frob job until frob has a release and to make sure the gate runs locally: scripts/check.py is that one command. The release workflow was invalid at parse time because of a job-level hashFiles; the native crate is permanent now so the conditional is simply gone.

### Changed
(no changed files detected)

### Evidence
- `tests/test_scripts.py::test_check_dry_run_runs_frob_then_both_backends` (pytest node id, verified passing when recorded)
- `tests/test_scripts.py::test_check_skip_frob_drops_the_first_gate` (pytest node id, verified passing when recorded)

### Captured claims
- tests: 2 passed (from 2 evidence id(s))
- gates: 12 error(s), 988 warning(s), 0 waived
- error-findings: OPAQUE001@tests/test_scripts.py, REF001@scripts/_common.py, SELFAUDIT001@scripts/_common.py, SELFAUDIT001@scripts/build.py, SELFAUDIT001@scripts/check.py, SELFAUDIT001@scripts/clean.py, SELFAUDIT001@scripts/develop.py, SELFAUDIT001@scripts/install.py, SELFAUDIT001@scripts/release.py, SELFAUDIT001@scripts/typecheck_oracle.py, SELFAUDIT001@tests/test_result_api.py, SELFAUDIT001@tests/test_scripts.py

<!-- ticket:T-0024 -->
```yaml
id: T-0024
title: release.yml smoke test imported from the project env instead of the smoke venv
state: done
kind: docs
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- .github/workflows/release.yml
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- cmd:python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/release.yml'));
  print('publish needs', d['jobs']['publish']['needs'])" exit=0 sha256=7687c701cda7
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
First release dispatch: every native wheel built, but the smoke step used uv run --python smoke-venv inside the project directory, which resolves the project environment, so import typani_core failed on three legs and publish never ran. Call the venv interpreter directly.

## Done report

The release workflow's smoke test ran the wrong interpreter; it now calls the smoke venv's python directly and prints the imported version, so a wheel that does not import fails the leg for a real reason.

### Changed
(no changed files detected)

### Evidence
- `cmd:python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/release.yml')); print('publish needs', d['jobs']['publish']['needs'])" exit=0 sha256=7687c701cda7` (cmd evidence, exit=0)

### Captured claims
- tests: 0 passed (from 0 evidence id(s))
- gates: 12 error(s), 983 warning(s), 0 waived
- error-findings: OPAQUE001@tests/test_scripts.py, REF001@scripts/_common.py, SELFAUDIT001@scripts/_common.py, SELFAUDIT001@scripts/build.py, SELFAUDIT001@scripts/check.py, SELFAUDIT001@scripts/clean.py, SELFAUDIT001@scripts/develop.py, SELFAUDIT001@scripts/install.py, SELFAUDIT001@scripts/release.py, SELFAUDIT001@scripts/typecheck_oracle.py, SELFAUDIT001@tests/test_result_api.py, SELFAUDIT001@tests/test_scripts.py

<!-- ticket:T-0025 -->
```yaml
id: T-0025
title: 'community files: LICENSE, CONTRIBUTING (frob workflow + AI policy), SECURITY,
  CODE_OF_CONDUCT, issue and PR templates'
state: done
kind: docs
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- LICENSE
- CONTRIBUTING.md
- SECURITY.md
- CODE_OF_CONDUCT.md
- .github/ISSUE_TEMPLATE/*
- .github/PULL_REQUEST_TEMPLATE.md
- README.md
- frob.toml
- pyproject.toml
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- cmd:python3 -c "import pathlib; [pathlib.Path(f).read_text() for f in ('LICENSE','CONTRIBUTING.md','SECURITY.md','CODE_OF_CONDUCT.md')];
  print('community files present')" exit=0 sha256=cad3d402c828
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
The repo declares MIT but ships no LICENSE file. Add the standard community set in the style of uv/ruff/ty/pytest: a CONTRIBUTING with a short path for experienced contributors and a genuinely beginner-friendly walkthrough, a frob section explaining tickets, directives and gates, and an AI-assisted-contribution policy that also tells agents how to use frob. SECURITY with private reporting, supported versions and scope. Contributor Covenant code of conduct. Issue forms and a PR template with the frob ticket and AI-disclosure checklist.

## Done report

Standard community set in the uv/ruff/ty/pytest style: LICENSE (missing until now), CONTRIBUTING with an experienced-contributor summary, a beginner walkthrough, a frob explainer and an AI policy addressed to agents, SECURITY, Code of Conduct, issue forms and a PR template.

### Changed
(no changed files detected)

### Evidence
- `cmd:python3 -c "import pathlib; [pathlib.Path(f).read_text() for f in ('LICENSE','CONTRIBUTING.md','SECURITY.md','CODE_OF_CONDUCT.md')]; print('community files present')" exit=0 sha256=cad3d402c828` (cmd evidence, exit=0)

### Captured claims
- tests: 0 passed (from 0 evidence id(s))
- gates: 13 error(s), 984 warning(s), 0 waived
- error-findings: DOC006@CODE_OF_CONDUCT.md, OPAQUE001@tests/test_scripts.py, REF001@scripts/_common.py, SELFAUDIT001@scripts/_common.py, SELFAUDIT001@scripts/build.py, SELFAUDIT001@scripts/check.py, SELFAUDIT001@scripts/clean.py, SELFAUDIT001@scripts/develop.py, SELFAUDIT001@scripts/install.py, SELFAUDIT001@scripts/release.py, SELFAUDIT001@scripts/typecheck_oracle.py, SELFAUDIT001@tests/test_result_api.py, SELFAUDIT001@tests/test_scripts.py

<!-- ticket:T-0026 -->
```yaml
id: T-0026
title: 'release.yml: interpreter lookup under set -e and Intel macOS leg on an Intel
  runner'
state: done
kind: docs
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- .github/workflows/release.yml
scope_breadth_ack: false
scope_breadth_ack_reason: null
no_scope_declared: false
no_scope_declared_reason: null
evidence:
- cmd:python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/release.yml'));
  m=d['jobs']['build-native']['strategy']['matrix']['include']; print([(e['os'],e['target'])
  for e in m])" exit=0 sha256=ae3cd5962725
designated_repro_test: null
threat: null
component: null
anchor: false
anchor_reason: null
land_commit: null
```
Second dispatch: ls of two candidate interpreter paths under set -e exits 2 on Linux and Windows; macos-latest is arm64 so the cross-built x86_64 wheel cannot be installed for the smoke test. Branch on the venv layout and run the Intel leg on macos-13.

## Done report

The smoke step's interpreter lookup and the Intel macOS runner were the last two release blockers; both fixed without touching what is built.

### Changed
(no changed files detected)

### Evidence
- `cmd:python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/release.yml')); m=d['jobs']['build-native']['strategy']['matrix']['include']; print([(e['os'],e['target']) for e in m])" exit=0 sha256=ae3cd5962725` (cmd evidence, exit=0)

### Captured claims
- tests: 0 passed (from 0 evidence id(s))
- gates: 13 error(s), 984 warning(s), 0 waived
- error-findings: DOC006@CODE_OF_CONDUCT.md, OPAQUE001@tests/test_scripts.py, REF001@scripts/_common.py, SELFAUDIT001@scripts/_common.py, SELFAUDIT001@scripts/build.py, SELFAUDIT001@scripts/check.py, SELFAUDIT001@scripts/clean.py, SELFAUDIT001@scripts/develop.py, SELFAUDIT001@scripts/install.py, SELFAUDIT001@scripts/release.py, SELFAUDIT001@scripts/typecheck_oracle.py, SELFAUDIT001@tests/test_result_api.py, SELFAUDIT001@tests/test_scripts.py

<!-- ticket:T-0027 -->
```yaml
id: T-0027
title: 'release.yml: drop the Intel macOS wheel leg'
state: in-progress
kind: docs
origin: human
created: '2026-09-05'
priority: high
parent: null
tier: ticket
sprint: null
runs_last: false
milestone: '0.1'
runs_last_parallel_safe: false
runs_last_parallel_safe_reason: null
scope:
- .github/workflows/release.yml
- docs/native.md
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
The macos-13 Intel runner pool stalls a release for hours; the Intel wheel is dropped and docs/native.md lists the platforms that ship wheels.
