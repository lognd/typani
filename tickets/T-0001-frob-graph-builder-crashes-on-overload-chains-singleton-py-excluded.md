---
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
---
frob 0.1.0a0's graph builder raises sqlite3.IntegrityError (UNIQUE constraint failed: symbols.symref) when parsing src/typani/singleton.py, which defines singleton() with two @typing.overload stubs plus the real implementation, all sharing the symref 'singleton'. Worked around by excluding src/typani/singleton.py from [graph] in frob.toml. Re-include once frob's graph builder dedupes overload stubs (or assigns distinct symrefs per overload) upstream in the frob repo itself.