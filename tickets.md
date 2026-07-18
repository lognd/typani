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
acceptance: []
threat: null
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
acceptance: []
threat: null
```
frob check currently runs with check_skip_ty=true (pyproject.toml [tool.frob]) because frob's bundled ty type checker reports 37 diagnostics across src/typani/{dispatch,error_set,singleton,sum}.py, tests/test_{dispatch,error_set,error_set_result,sum,unit}.py, and examples/{error_sets,sum_dispatch}.py that mypy (the project's actual type checker, see Makefile typecheck target) does not flag. This is pre-existing typing debt uncovered by adopting frob, not something introduced by the frob adoption pass -- no source changes were made to fix it (out of scope for T-adoption). Triage each diagnostic: either it is a real bug mypy is missing (fix the code) or a mypy/ty divergence worth an explicit ty config (pyproject.toml [tool.ty] ignore) once the project decides whether to standardize on ty. Re-enable ty in frob check (drop check_skip_ty) once resolved.

<!-- ticket:T-0003 -->
```yaml
id: T-0003
title: 'frob compliance: zero warnings'
state: done
kind: feature
origin: agent
created: '2026-07-17'
blocked_by: []
parent: null
scope:
- src/typani/**,docs/**,tests/**
evidence:
- tests/test_build.py::test_package_imports
attachments: []
acceptance: []
threat: null
```
## Done report

Changed: dispatch.py::dispatch, sum.py::Sum/.match/.check, unit.py::Unit/UnitMeta,
unreachable.py::Unreachable, error_set.py::ErrorSet/.description,
result.py::Result/.map/.map_err/.and_then/.or_else/.inspect/.swap_err/.swap_ok/.ok,
docs/{dispatch,sum,unit,unreachable,singleton}.md, docs/index.md (new),
tests/{test_result,test_error_set_result,test_build,test_sum,test_unreachable}.py,
pyproject.toml (pytest-cov dev dep, real editable install).
Evidence: pytest -q all green; frob check --stamp-coverage (TEST006 cleared).
Filed: none (all findings were fixable in scope).
Gates: frob check went from 5 errors/46 warnings to 0 errors/25 warnings.
Remaining 25 are all COV001 on class methods -- see FROB GAP in the
compliance report; frob attributes a `frob:doc` comment placed directly
above a nested `def` inside a class to the enclosing class symbol, not
the method, so per-method doc coverage cannot be satisfied as designed.
No waiver applies (not algorithm-inherent); left unfixed per protocol.

<!-- ticket:T-0004 -->
```yaml
id: T-0004
title: 'frob compliance: T-0044 workaround for method-level COV001'
state: done
kind: feature
origin: agent
created: '2026-07-17'
blocked_by: []
parent: null
scope:
- src/typani/**
evidence:
- tests/test_build.py::test_package_imports
attachments: []
acceptance: []
threat: null
```
## Done report

Changed: applied the T-0044 workaround (frob:doc as the first statement
inside the method/class body, right after the docstring, instead of
above the def) to the 25 remaining COV001 findings: error_set.py::
ErrorSet.description, sum.py::Sum.match/.check, result.py::Result and
its map/map_err/and_then/or_else/inspect/is_ok/ok/danger_ok/is_err/err/
danger_err/swap_err/swap_ok, option.py::Option.is_some/is_nothing/some/
danger_some/map/and_then/or_else/inspect/unwrap_or. Added frob:ticket
T-0004 edges to every symbol touched.
Evidence: pytest -q all green; frob check --stamp-coverage refreshed.
Filed: none further (gaps 2 and 3 already tracked as T-0100/T-0101 by
the orchestrator).
Gates: frob check . -> PASS, 0 errors, 0 warnings.

<!-- ticket:T-0005 -->
```yaml
id: T-0005
title: 'typani.strata design model: TEST001/TEST003 unit+integration coverage debt'
state: queued
kind: docs
origin: agent
created: '2026-07-18'
blocked_by: []
parent: null
scope:
- design/typani.strata
evidence: []
attachments: []
acceptance: []
threat: null
```
The typani.strata pilot design model (first sibling-repo strata rollout, T-0150-style self-model exercise) has 12 flow nodes and 1 interface-level TEST003 gap with no frob:tests binding. TEST001/TEST003 are warn-severity per frob.toml's legacy-adoption baseline, matching COV001/TEST00x already warned there for src/typani/**. Deferred rather than fixed in the same pass as the model itself: writing property/unit tests against strata flow declarations (frob:tests kind="unit"/"integration") is new territory for this repo and should get its own scoped pass once the strata model has stabilized, not be rushed to silence warnings on first landing.
