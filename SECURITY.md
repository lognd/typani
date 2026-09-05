# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | yes       |
| 0.0.x   | no        |

Only the latest 0.1.x release receives security fixes. Upgrade before
filing a report if you are on 0.0.x.

## Reporting a vulnerability

Please do not file a public GitHub issue for a suspected vulnerability.

Use one of the following, in order of preference:

1. GitHub private vulnerability reporting: open the "Security" tab on
   [lognd/typani](https://github.com/lognd/typani), then "Report a
   vulnerability". This creates a private advisory thread that only the
   maintainer and you can see.
2. Email logan@logand.app if you cannot use GitHub's reporting flow.

### What to include

- A minimal reproduction (code snippet or a small script).
- The typani version and backend (`python -c "import typani; print(typani.__version__, typani.backend_name())"`).
- Python version and operating system.
- What you expected versus what happened, and why you believe it is a
  security issue rather than a correctness bug.

### Response expectations

The maintainer aims to acknowledge a report within 7 days. There is no
bounty program. A fix timeline depends on severity and will be discussed
with you in the private advisory thread.

## Scope notes specific to this library

typani is an in-memory value-type library with no network access, no
file I/O beyond what a caller explicitly does with the values it hands
back, and no code execution of untrusted input in its normal (non-lint)
code paths. Given that shape, most legitimate reports will fall into one
of these areas:

- **The native extension.** The optional `typani-core` crate
  (`crates/typani-core`) is a PyO3 extension. `unsafe_code = "forbid"`
  is set at the crate level, so memory-safety issues would most likely
  come from the PyO3 Python/Rust boundary itself rather than hand-written
  unsafe code. Reports here should include whether the issue reproduces
  under the pure-Python backend (`TYPANI_PURE=1`) as well.
- **The backend selector.** `typani._impl` chooses between the native
  and pure-Python backends at import time based on `typani_core`
  being importable and version-matched to `typani` itself, and falls
  back to pure-Python on any mismatch or forced `TYPANI_PURE=1`. A
  report claiming the selector picks an incompatible or stale backend
  should include the exact versions of both packages involved.
- **Pickling.** `Ok`/`Err`/`Some`/`Nothing` are picklable. Unpickling
  untrusted data is never safe in Python regardless of typani; this is
  not typani-specific and will be closed as out of scope unless typani's
  own `__reduce__`/`__setstate__` implementation does something beyond
  the standard unsafe-by-design pickle contract (for example, executing
  code during unpickling that a plain attribute-restoring `__setstate__`
  would not).
- **`typani.lint`.** `python -m typani.lint` parses source files with
  `ast.parse` only; it never executes, imports, or evaluates the code it
  scans. A report claiming otherwise (arbitrary code execution while
  linting a file) is treated as high severity.

If you are unsure whether something is in scope, report it anyway and
let the maintainer make the call -- a false positive costs little, a
missed report costs a lot.
