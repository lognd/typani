//! typani-core: native Result/Option kernels for typani (T-0010).
//!
//! Frozen PyO3 pyclasses that mirror src/typani/result.py and
//! src/typani/option.py exactly -- same methods, same error types, same
//! error MESSAGES, same pickling/repr/hash/eq behavior. `typani/_impl.py`
//! chooses this module over the pure-Python implementation when it is
//! importable and its `__version__` matches typani's own; on any mismatch
//! or ImportError the pure-Python classes are used instead, so this crate
//! is purely an accelerator, never a required dependency.

use pyo3::prelude::*;

mod option;
mod result;

/// BIND: __version__: str
///
/// WHY: `typani._impl.native_active()` compares this against typani's own
/// `__version__` (src/typani/_version.py) before trusting this extension;
/// an ABI-coupled native module with a stale version is worse than no
/// native module, so the check must have something exact to compare.
#[pymodule]
fn typani_core(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    result::register(py, m)?;
    option::register(py, m)?;
    Ok(())
}
