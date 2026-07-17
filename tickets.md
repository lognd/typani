# Tickets

Central ledger managed by `frob ticket` -- one section per ticket.

<!-- ticket:T-0001 -->
```yaml
id: T-0001
title: frob graph builder crashes on @overload chains (singleton.py excluded)
state: queued
kind: bug
origin: human
created: '2026-07-17'
blocked_by: []
parent: null
scope:
- src/typani/singleton.py
evidence: []
attachments: []
```
frob 0.1.0a0's graph builder raises sqlite3.IntegrityError (UNIQUE constraint failed: symbols.symref) when parsing src/typani/singleton.py, which defines singleton() with two @typing.overload stubs plus the real implementation, all sharing the symref 'singleton'. Worked around by excluding src/typani/singleton.py from [graph] in frob.toml. Re-include once frob's graph builder dedupes overload stubs (or assigns distinct symrefs per overload) upstream in the frob repo itself.

<!-- ticket:T-0002 -->
```yaml
id: T-0002
title: reconcile ty diagnostics with mypy baseline (frob check --skip-ty active)
state: queued
kind: bug
origin: human
created: '2026-07-17'
blocked_by: []
parent: null
scope:
- src/typani/**,tests/**,examples/**
evidence: []
attachments: []
```
frob check currently runs with check_skip_ty=true (pyproject.toml [tool.frob]) because frob's bundled ty type checker reports 37 diagnostics across src/typani/{dispatch,error_set,singleton,sum}.py, tests/test_{dispatch,error_set,error_set_result,sum,unit}.py, and examples/{error_sets,sum_dispatch}.py that mypy (the project's actual type checker, see Makefile typecheck target) does not flag. This is pre-existing typing debt uncovered by adopting frob, not something introduced by the frob adoption pass -- no source changes were made to fix it (out of scope for T-adoption). Triage each diagnostic: either it is a real bug mypy is missing (fix the code) or a mypy/ty divergence worth an explicit ty config (pyproject.toml [tool.ty] ignore) once the project decides whether to standardize on ty. Re-enable ty in frob check (drop check_skip_ty) once resolved.
