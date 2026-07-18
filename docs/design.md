# Design model

`design/typani.strata` is a [strata](https://github.com/) design model --
frob's provable system-design language -- that models typani's real module
graph as enforced truth: one `node` per `src/typani/*.py` file, one `flow`
per real `from typani.X import ...` edge, and a handful of `assert`
claims (`reach`/`noflow`) that hold of the actual code today.

## Why this exists

typani is a pure, in-memory value-type library with no filesystem,
network, process, or dynamic-eval I/O anywhere in `src/typani/` (verified
by direct grep for `subprocess`/`os.system`/`open(`/`socket`/`requests`/
`urllib`/`eval(`/`exec(`/`__import__`/`os.environ` -- zero matches). Every
node in `design/typani.strata` therefore declares **no `may` capabilities
at all**. That absence is itself the proven claim: `frob sys audit`'s
self-conformance check (SYS101) would flag a stale `may` declaration the
moment any node's code actually gained an unmeasured capability, so the
near-zero capability surface stays exactly as falsifiable as a populated
one would be.

## Keeping it green

Re-run the audit after touching anything under `src/typani/` or
`design/typani.strata`:

```sh
frob sys audit .
```

A clean run ends with:

```
sys audit: PROVED -- zero gaps across every configured view
sys audit: self-conformance PROVED -- zero SYS gaps
```

`frob check` also runs the same model as its `sys` gate stage (see
`frob check --only sys` to isolate it). If you add, remove, or rename a
module under `src/typani/`, update the matching `node`'s `code` glob in
`design/typani.strata` and add/remove the corresponding `flow` lines for
any new or removed `from typani.X import ...` edges -- the model is only
useful as long as it matches the real import graph, not an aspirational
one.

Every declaration in `design/typani.strata` carries a `frob:doc` anchor
back into `docs/*.md` and a `frob:ticket T-0005` edge (tracked debt: the
model's flows/interface do not yet have `frob:tests` bindings, see
`tickets.md`). `TEST001`/`TEST003` on the design model are warn-severity
in `frob.toml`, matching the same legacy-adoption baseline posture already
applied to `COV001`/`TEST00x` on `src/typani/**`.
