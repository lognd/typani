# Design model

`design/typani.strata` is a [strata](https://github.com/) design model --
frob's provable system-design language -- that models typani's real module
graph as enforced truth: one `node` per `src/typani/*.py` file (plus one
`lint` node for `src/typani/lint/**`), one `flow` per real
`from typani.X import ...` edge -- including the lazy, in-method imports
`result.py`/`option.py`/`_exceptions.py` use to break their import cycle
-- and a handful of `assert` claims (`reach`/`noflow`) that hold of the
actual code today.

T-0013 extended the original eight-node survey with the modules split out
during the 0.1 redesign: `_exceptions.py` (`UnwrapError`), `_propagate.py`
(`@propagate`/`@catching`), `_impl.py` (native/pure backend selection),
`_version.py` (the version single-source-of-truth), and `lint/**` (the
opt-in misuse checker, modeled with no inbound or outbound flow since it
is deliberately never imported from `typani/__init__.py`).

## Why this exists

typani is a pure, in-memory value-type library with no filesystem,
network, process, or dynamic-eval I/O anywhere in `src/typani/` (verified
by direct grep for `subprocess`/`os.system`/`open(`/`socket`/`requests`/
`urllib`/`eval(`/`exec(`/`__import__` -- zero matches). Every node except
two therefore declares **no `may` capabilities at all**. The two
exceptions are declared, not hidden: `impl_mod` (`_impl.py`) reads the
`TYPANI_PURE` environment variable to select the native/pure backend
(`may "env.read"`), and `lint` (`lint/__init__.py`) reads `*.py` source
files from disk to lint them (`may "fs-read"`). That near-zero surface,
and the two narrow grants that are the whole exception to it, are the
proven claim: `frob sys audit`'s self-conformance check (SYS100/SYS101)
would flag a stale `may` the moment any node's code diverged from what is
declared here, in either direction -- a missing grant or an unused one.

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
