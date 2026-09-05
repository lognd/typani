# typani documentation

Index of the module-level guides. Each guide describes one public
interface; see the module docstring in the corresponding source file for
the authoritative API surface.

**Start here:** the [README](../README.md#sixty-second-tour) has a
sixty-second tour that runs end to end; [redesign-0.1.md](redesign-0.1.md)
is the design record behind every 0.1 decision (the usage audit, the bug
themes it traces to, and what changed since 0.0.x).

| Module | Purpose | Doc |
|--------|---------|-----|
| `typani.result` | `Result[T, E]`, Rust-inspired success/error value | [result.md](result.md) |
| `typani.option` | `Option[T]`, explicit optional value | [option.md](option.md) |
| `typani._exceptions` | `UnwrapError`, raised by unwrap/danger_* misuse | [result.md#unwraperror](result.md#unwraperror) |
| `typani._propagate` | `@propagate` / `@catching`, early-return and exception-boundary decorators | [result.md#propagation](result.md#propagation) |
| `typani._impl` | Native/pure-Python backend selection (`native_active`, `backend_name`) | [native.md](native.md) |
| `typani.error_set` | Zig-inspired typed error enum | [error_set.md](error_set.md) |
| `typani.sum` | Tagged union with exhaustive dispatch | [sum.md](sum.md) |
| `typani.dispatch` | Type-based dispatch helper | [dispatch.md](dispatch.md) |
| `typani.unit` | Zero-slot marker base class | [unit.md](unit.md) |
| `typani.unreachable` | Runtime-checked unreachable sentinel | [unreachable.md](unreachable.md) |
| `typani.singleton` | Singleton decorator and base classes | [singleton.md](singleton.md) |
| `typani.lint` | stdlib-only misuse checker, `python -m typani.lint` | [lint.md](lint.md) |
| `typani_core` (native) | PyO3/maturin accelerator for Result/Option, pure-Python fallback | [native.md](native.md) |
| -- | `design/typani.strata`, the provable system-design model of typani's own module graph | [design.md](design.md) |
