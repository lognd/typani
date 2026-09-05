//! Native `Result`/`Ok`/`Err`, mirroring src/typani/result.py exactly.

use pyo3::exceptions::PyTypeError;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyBool, PyTuple, PyType};
use pyo3::{intern, prelude::*, IntoPyObjectExt};

/// Lazily-imported `typani._exceptions.UnwrapError`, cached for the process.
///
/// BIND: (lazy import, no Rust signature)
///
/// WHY: `UnwrapError` stays a pure-Python class (per T-0010 spec) so
/// `@propagate` and user `except UnwrapError` clauses work unchanged
/// against both backends; importing it eagerly at module-load time would
/// risk a circular import with `typani.__init__`, so the import is
/// deferred to first use and cached in a `PyOnceLock`.
static UNWRAP_ERROR: PyOnceLock<Py<PyType>> = PyOnceLock::new();

fn unwrap_error_type(py: Python<'_>) -> PyResult<&Bound<'_, PyType>> {
    let cell = UNWRAP_ERROR.get_or_try_init(py, || -> PyResult<Py<PyType>> {
        let module = py.import("typani._exceptions")?;
        let cls = module.getattr("UnwrapError")?;
        cls.extract::<Py<PyType>>().map_err(PyErr::from)
    })?;
    Ok(cell.bind(py))
}

/// Raise `UnwrapError(container, message)` with the same constructor shape
/// as the pure-Python class, so `exc.container` and `str(exc)` match.
fn unwrap_error(py: Python<'_>, container: Bound<'_, PyAny>, message: Option<&str>) -> PyErr {
    match unwrap_error_type(py) {
        Ok(cls) => {
            let args = match message {
                Some(msg) => PyTuple::new(
                    py,
                    [container, pyo3::types::PyString::new(py, msg).into_any()],
                ),
                None => PyTuple::new(py, [container]),
            };
            match args {
                Ok(args) => match cls.call1(args) {
                    Ok(exc) => PyErr::from_value(exc),
                    Err(err) => err,
                },
                Err(err) => err,
            }
        }
        Err(err) => err,
    }
}

/// Cached `types.GenericAlias` type, used by `__class_getitem__`.
static GENERIC_ALIAS: PyOnceLock<Py<PyType>> = PyOnceLock::new();

fn generic_alias<'py>(
    py: Python<'py>,
    cls: Bound<'py, PyType>,
    args: Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let alias_cls = GENERIC_ALIAS.get_or_try_init(py, || -> PyResult<Py<PyType>> {
        let module = py.import("types")?;
        let cls = module.getattr("GenericAlias")?;
        cls.extract::<Py<PyType>>().map_err(PyErr::from)
    })?;
    alias_cls.bind(py).call1((cls, args))
}

/// BIND: class Result(Generic[T_co, E_co])
///
/// WHY: abstract base of `Ok`/`Err`; frozen and subclassable so
/// `isinstance(r, Result)` and `match r: case Ok(v): ...` narrowing work
/// exactly as they do against the pure-Python base.
#[pyclass(name = "Result", module = "typani.result", subclass, frozen)]
struct ResultBase;

#[pymethods]
impl ResultBase {
    #[new]
    #[pyo3(signature = (*_args, **_kwargs))]
    fn new(
        py: Python<'_>,
        _args: &Bound<'_, PyTuple>,
        _kwargs: Option<&Bound<'_, pyo3::types::PyDict>>,
    ) -> PyResult<Self> {
        let _ = py;
        Err(PyTypeError::new_err(
            "Result is abstract; construct Ok(value) or Err(error)",
        ))
    }

    #[classmethod]
    #[pyo3(signature = (fn_, *exceptions, on_error))]
    fn catch(
        cls: &Bound<'_, PyType>,
        fn_: Bound<'_, PyAny>,
        exceptions: Bound<'_, PyTuple>,
        on_error: Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let py = cls.py();
        let caught: Bound<'_, PyAny> = if exceptions.is_empty() {
            py.get_type::<pyo3::exceptions::PyException>().into_any()
        } else {
            exceptions.into_any()
        };
        match fn_.call0() {
            Ok(value) => make_ok(py, value),
            Err(err) => {
                let is_match = err.matches(py, &caught).unwrap_or(false);
                if !is_match {
                    return Err(err);
                }
                let exc_value = err.value(py).clone().into_any();
                let error = on_error.call1((exc_value,))?;
                make_err(py, error, PyTuple::empty(py).unbind())
            }
        }
    }

    #[classmethod]
    fn __class_getitem__<'py>(
        cls: &Bound<'py, PyType>,
        args: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let py = cls.py();
        generic_alias(py, cls.clone(), args)
    }
}

pub(crate) fn make_ok(py: Python<'_>, value: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let init = PyClassInitializer::from(ResultBase).add_subclass(OkClass {
        value: value.unbind(),
    });
    Py::new(py, init).map(|p| p.into_any())
}

pub(crate) fn make_err(
    py: Python<'_>,
    error: Bound<'_, PyAny>,
    notes: Py<PyTuple>,
) -> PyResult<Py<PyAny>> {
    make_err_traced(py, error, notes, PyTuple::empty(py).unbind())
}

pub(crate) fn make_err_traced(
    py: Python<'_>,
    error: Bound<'_, PyAny>,
    notes: Py<PyTuple>,
    trace: Py<PyTuple>,
) -> PyResult<Py<PyAny>> {
    let init = PyClassInitializer::from(ResultBase).add_subclass(ErrClass {
        error: error.unbind(),
        notes,
        trace,
    });
    Py::new(py, init).map(|p| p.into_any())
}

/// BIND: class Ok(Result[T_co, E_co])
///
/// WHY: success variant; holds the payload directly (no boxing beyond the
/// `Py<PyAny>` GC handle already required) so `unwrap`/`danger_ok` are a
/// single field read with no Python-level attribute lookup.
#[pyclass(name = "Ok", module = "typani.result", extends = ResultBase, frozen)]
struct OkClass {
    value: Py<PyAny>,
}

#[pymethods]
impl OkClass {
    #[new]
    fn new(value: Bound<'_, PyAny>) -> PyClassInitializer<Self> {
        PyClassInitializer::from(ResultBase).add_subclass(OkClass {
            value: value.unbind(),
        })
    }

    #[classattr]
    fn __match_args__(py: Python<'_>) -> Py<PyTuple> {
        PyTuple::new(py, ["value"]).unwrap().unbind()
    }

    #[getter]
    fn value(&self, py: Python<'_>) -> Py<PyAny> {
        self.value.clone_ref(py)
    }

    #[getter]
    fn is_ok(&self) -> bool {
        true
    }

    #[getter]
    fn is_err(&self) -> bool {
        false
    }

    #[getter]
    fn ok(&self, py: Python<'_>) -> Py<PyAny> {
        self.value.clone_ref(py)
    }

    #[getter]
    fn err(&self, py: Python<'_>) -> Py<PyAny> {
        py.None()
    }

    #[getter]
    fn danger_ok(&self, py: Python<'_>) -> Py<PyAny> {
        self.value.clone_ref(py)
    }

    #[getter]
    fn danger_err(self_: &Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(self_.py(), self_.clone().into_any(), None))
    }

    #[getter]
    fn notes(&self, py: Python<'_>) -> Py<PyTuple> {
        PyTuple::empty(py).unbind()
    }

    #[getter]
    fn trace(&self, py: Python<'_>) -> Py<PyTuple> {
        PyTuple::empty(py).unbind()
    }

    fn is_ok_and(&self, py: Python<'_>, pred: Bound<'_, PyAny>) -> PyResult<bool> {
        pred.call1((self.value.bind(py),))?.is_truthy()
    }

    fn is_err_and(&self, _pred: Bound<'_, PyAny>) -> bool {
        false
    }

    /// BIND: unwrap(self, *, err=None, note=None) -> T -- T-0028 keyword sugar.
    /// *err*/*note* are always ignored on `Ok`; the bare path (both None)
    /// takes the same single-field-read branch as before.
    #[pyo3(signature = (*, err=None, note=None))]
    fn unwrap(
        &self,
        py: Python<'_>,
        err: Option<Bound<'_, PyAny>>,
        note: Option<Bound<'_, PyAny>>,
    ) -> Py<PyAny> {
        let _ = (err, note);
        self.value.clone_ref(py)
    }

    fn unwrap_err(self_: &Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(self_.py(), self_.clone().into_any(), None))
    }

    fn unwrap_or(&self, py: Python<'_>, _default: Bound<'_, PyAny>) -> Py<PyAny> {
        self.value.clone_ref(py)
    }

    fn unwrap_or_else(&self, py: Python<'_>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self.value.clone_ref(py)
    }

    fn expect(&self, py: Python<'_>, _msg: &str) -> Py<PyAny> {
        self.value.clone_ref(py)
    }

    fn expect_err(self_: &Bound<'_, Self>, msg: &str) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(
            self_.py(),
            self_.clone().into_any(),
            Some(msg),
        ))
    }

    fn map(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let mapped = fn_.call1((self.value.bind(py),))?;
        make_ok(py, mapped)
    }

    fn map_err(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn and_then(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        Ok(fn_.call1((self.value.bind(py),))?.unbind())
    }

    fn or_else(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn inspect(self_: &Bound<'_, Self>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let self_ref = self_.borrow();
        fn_.call1((self_ref.value.bind(self_.py()),))?;
        Ok(self_.clone().into_any().unbind())
    }

    fn inspect_err(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn fold(
        &self,
        py: Python<'_>,
        on_ok: Bound<'_, PyAny>,
        _on_err: Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        Ok(on_ok.call1((self.value.bind(py),))?.unbind())
    }

    fn to_option(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        crate::option::make_some(py, self.value.bind(py).clone())
    }

    fn note(self_: &Bound<'_, Self>, _msg: &str) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    /// BIND: wrap_err(self, err) -> Result[T, F] -- no-op on Ok, T-0028.
    fn wrap_err(self_: &Bound<'_, Self>, _err: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    /// BIND: traced(self, site: str) -> Result[T, E] -- no-op on Ok, T-0028.
    fn traced(self_: &Bound<'_, Self>, _site: &str) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn swap_err(self_: &Bound<'_, Self>, _err: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn swap_ok(self_: &Bound<'_, Self>, _ok: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(self_.py(), self_.clone().into_any(), None))
    }

    fn __or__(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        self.map(py, fn_)
    }

    fn __rshift__(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        self.and_then(py, fn_)
    }

    fn __iter__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let list = pyo3::types::PyList::new(py, [self.value.bind(py)])?;
        Ok(list.try_iter()?.unbind().into_any())
    }

    fn __bool__(&self) -> PyResult<bool> {
        Err(PyTypeError::new_err(
            "Result has no truth value; use is_ok/is_err or match",
        ))
    }

    fn __eq__(&self, py: Python<'_>, other: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        match other.cast::<OkClass>() {
            std::result::Result::Ok(other_v) => {
                let eq = self.value.bind(py).eq(other_v.borrow().value.bind(py))?;
                Ok(PyBool::new(py, eq).to_owned().unbind().into_any())
            }
            std::result::Result::Err(_) => Ok(py.NotImplemented()),
        }
    }

    fn __ne__(&self, py: Python<'_>, other: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let eq = self.__eq__(py, other)?;
        if eq.bind(py).is(py.NotImplemented()) {
            return Ok(eq);
        }
        let truthy = eq.bind(py).is_truthy().unwrap_or(true);
        Ok(PyBool::new(py, !truthy).to_owned().unbind().into_any())
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        let tuple = (0isize, self.value.bind(py));
        tuple.into_pyobject(py)?.hash()
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        let r = self.value.bind(py).repr()?;
        Ok(format!("Ok({})", r))
    }

    fn __str__(&self, py: Python<'_>) -> PyResult<String> {
        let s = self.value.bind(py).str()?;
        Ok(format!("Ok({})", s))
    }

    fn __reduce__(self_: &Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        let py = self_.py();
        let cls = self_.get_type();
        let args = PyTuple::new(py, [self_.borrow().value.bind(py)])?;
        (cls, args).into_py_any(py)
    }

    fn __copy__(self_: &Bound<'_, Self>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn __deepcopy__(&self, py: Python<'_>, memo: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let copy_mod = py.import("copy")?;
        let deep = copy_mod.getattr(intern!(py, "deepcopy"))?;
        let copied = deep.call1((self.value.bind(py), memo))?;
        make_ok(py, copied)
    }
}

/// BIND: class Err(Result[T_co, E_co])
///
/// WHY: failure variant; carries `notes` alongside the error payload so
/// `note()`/`map_err()` and `__reduce__`'s `_rebuild_err` round-trip
/// exactly like the pure-Python `Err`.
#[pyclass(name = "Err", module = "typani.result", extends = ResultBase, frozen)]
struct ErrClass {
    error: Py<PyAny>,
    notes: Py<PyTuple>,
    /// Error-return trace (T-0028): propagation sites, innermost first.
    /// Not part of equality/hash; see `traced()`.
    trace: Py<PyTuple>,
}

#[pymethods]
impl ErrClass {
    #[new]
    fn new(py: Python<'_>, error: Bound<'_, PyAny>) -> PyClassInitializer<Self> {
        PyClassInitializer::from(ResultBase).add_subclass(ErrClass {
            error: error.unbind(),
            notes: PyTuple::empty(py).unbind(),
            trace: PyTuple::empty(py).unbind(),
        })
    }

    #[classattr]
    fn __match_args__(py: Python<'_>) -> Py<PyTuple> {
        PyTuple::new(py, ["error"]).unwrap().unbind()
    }

    #[getter]
    fn error(&self, py: Python<'_>) -> Py<PyAny> {
        self.error.clone_ref(py)
    }

    #[getter]
    fn notes(&self, py: Python<'_>) -> Py<PyTuple> {
        self.notes.clone_ref(py)
    }

    #[getter]
    fn trace(&self, py: Python<'_>) -> Py<PyTuple> {
        self.trace.clone_ref(py)
    }

    #[getter]
    fn is_ok(&self) -> bool {
        false
    }

    #[getter]
    fn is_err(&self) -> bool {
        true
    }

    #[getter]
    fn ok(&self, py: Python<'_>) -> Py<PyAny> {
        py.None()
    }

    #[getter]
    fn err(&self, py: Python<'_>) -> Py<PyAny> {
        self.error.clone_ref(py)
    }

    #[getter]
    fn danger_ok(self_: &Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(self_.py(), self_.clone().into_any(), None))
    }

    #[getter]
    fn danger_err(&self, py: Python<'_>) -> Py<PyAny> {
        self.error.clone_ref(py)
    }

    fn is_ok_and(&self, _pred: Bound<'_, PyAny>) -> bool {
        false
    }

    fn is_err_and(&self, py: Python<'_>, pred: Bound<'_, PyAny>) -> PyResult<bool> {
        pred.call1((self.error.bind(py),))?.is_truthy()
    }

    /// BIND: unwrap(self, *, err=None, note=None) -> T -- T-0028 keyword sugar.
    /// With `err` given, the raised error's `.container` is
    /// `self.wrap_err(err)` (further `.note(note)`-d if given); with only
    /// `note`, it is `self.note(note)`. Bare (both None) is the original
    /// fast path: raise immediately, nothing else touched.
    #[pyo3(signature = (*, err=None, note=None))]
    fn unwrap(
        self_: &Bound<'_, Self>,
        err: Option<Bound<'_, PyAny>>,
        note: Option<Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let py = self_.py();
        if err.is_none() && note.is_none() {
            return Err(unwrap_error(py, self_.clone().into_any(), None));
        }
        let mut container: Bound<'_, PyAny> = match err {
            Some(new_err) => self_.call_method1(intern!(py, "wrap_err"), (new_err,))?,
            None => self_.clone().into_any(),
        };
        if let Some(msg) = note {
            container = container.call_method1(intern!(py, "note"), (msg,))?;
        }
        Err(unwrap_error(py, container, None))
    }

    fn unwrap_err(&self, py: Python<'_>) -> Py<PyAny> {
        self.error.clone_ref(py)
    }

    fn unwrap_or(&self, default: Bound<'_, PyAny>) -> Py<PyAny> {
        default.unbind()
    }

    fn unwrap_or_else(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        Ok(fn_.call1((self.error.bind(py),))?.unbind())
    }

    fn expect(self_: &Bound<'_, Self>, msg: &str) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(
            self_.py(),
            self_.clone().into_any(),
            Some(msg),
        ))
    }

    fn expect_err(&self, py: Python<'_>, _msg: &str) -> Py<PyAny> {
        self.error.clone_ref(py)
    }

    fn map(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn map_err(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let mapped = fn_.call1((self.error.bind(py),))?;
        make_err_traced(
            py,
            mapped,
            self.notes.clone_ref(py),
            self.trace.clone_ref(py),
        )
    }

    fn and_then(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn or_else(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        Ok(fn_.call1((self.error.bind(py),))?.unbind())
    }

    fn inspect(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn inspect_err(self_: &Bound<'_, Self>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let self_ref = self_.borrow();
        fn_.call1((self_ref.error.bind(self_.py()),))?;
        Ok(self_.clone().into_any().unbind())
    }

    fn fold(
        &self,
        py: Python<'_>,
        _on_ok: Bound<'_, PyAny>,
        on_err: Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        Ok(on_err.call1((self.error.bind(py),))?.unbind())
    }

    fn to_option(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        crate::option::make_nothing(py)
    }

    fn note(&self, py: Python<'_>, msg: &str) -> PyResult<Py<PyAny>> {
        let mut notes: Vec<Bound<'_, PyAny>> = self.notes.bind(py).iter().collect();
        notes.push(msg.into_pyobject(py)?.into_any());
        let new_notes = PyTuple::new(py, notes)?.unbind();
        make_err_traced(
            py,
            self.error.bind(py).clone(),
            new_notes,
            self.trace.clone_ref(py),
        )
    }

    /// BIND: wrap_err(self, err) -> Result[T, F] -- T-0028
    ///
    /// WHY: unlike map_err, *err* is a plain replacement value, not a
    /// function of the old error; the old error is preserved as a new
    /// trailing note (`"caused by {inner!r}"`) instead of being lost.
    fn wrap_err(&self, py: Python<'_>, err: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let cause = self.error.bind(py).repr()?;
        let cause_note = format!("caused by {cause}");
        let mut notes: Vec<Bound<'_, PyAny>> = self.notes.bind(py).iter().collect();
        notes.push(cause_note.into_pyobject(py)?.into_any());
        let new_notes = PyTuple::new(py, notes)?.unbind();
        make_err_traced(py, err, new_notes, self.trace.clone_ref(py))
    }

    /// BIND: traced(self, site: str) -> Result[T, E] -- T-0028
    ///
    /// WHY: appends *site* to the error-return trace, innermost first;
    /// called once per hop by `typani.propagate`. Preserves notes.
    fn traced(&self, py: Python<'_>, site: &str) -> PyResult<Py<PyAny>> {
        let mut trace: Vec<Bound<'_, PyAny>> = self.trace.bind(py).iter().collect();
        trace.push(site.into_pyobject(py)?.into_any());
        let new_trace = PyTuple::new(py, trace)?.unbind();
        make_err_traced(
            py,
            self.error.bind(py).clone(),
            self.notes.clone_ref(py),
            new_trace,
        )
    }

    /// BIND: _with_meta(self, notes: tuple[str, ...], trace: tuple[str, ...] = ()) -> Err
    ///
    /// WHY: `typani.result._rebuild_err` (pure Python, shared by both
    /// backends' `__reduce__`) calls `Err(error)._with_meta(notes, trace)`
    /// to restore notes/trace during unpickling; the pure-Python `Err`
    /// mutates and returns `self`, but this class is frozen, so it returns
    /// a fresh instance with the same error and the given notes/trace.
    #[pyo3(signature = (notes, trace=None))]
    fn _with_meta(
        &self,
        py: Python<'_>,
        notes: Bound<'_, PyTuple>,
        trace: Option<Bound<'_, PyTuple>>,
    ) -> PyResult<Py<PyAny>> {
        let trace = trace.unwrap_or_else(|| PyTuple::empty(py));
        make_err_traced(
            py,
            self.error.bind(py).clone(),
            notes.unbind(),
            trace.unbind(),
        )
    }

    fn swap_err(self_: &Bound<'_, Self>, _err: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(self_.py(), self_.clone().into_any(), None))
    }

    fn swap_ok(self_: &Bound<'_, Self>, _ok: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn __or__(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn __rshift__(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn __iter__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let list = pyo3::types::PyList::empty(py);
        Ok(list.try_iter()?.unbind().into_any())
    }

    fn __bool__(&self) -> PyResult<bool> {
        Err(PyTypeError::new_err(
            "Result has no truth value; use is_ok/is_err or match",
        ))
    }

    fn __eq__(&self, py: Python<'_>, other: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        match other.cast::<ErrClass>() {
            std::result::Result::Ok(other_v) => {
                let eq = self.error.bind(py).eq(other_v.borrow().error.bind(py))?;
                Ok(PyBool::new(py, eq).to_owned().unbind().into_any())
            }
            std::result::Result::Err(_) => Ok(py.NotImplemented()),
        }
    }

    fn __ne__(&self, py: Python<'_>, other: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let eq = self.__eq__(py, other)?;
        if eq.bind(py).is(py.NotImplemented()) {
            return Ok(eq);
        }
        let truthy = eq.bind(py).is_truthy().unwrap_or(true);
        Ok(PyBool::new(py, !truthy).to_owned().unbind().into_any())
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        let tuple = (1isize, self.error.bind(py));
        tuple.into_pyobject(py)?.hash()
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        let r = self.error.bind(py).repr()?;
        Ok(self.render_notes(py, format!("Err({})", r)))
    }

    fn __str__(&self, py: Python<'_>) -> PyResult<String> {
        let s = self.error.bind(py).str()?;
        Ok(self.render_notes(py, format!("Err({})", s)))
    }

    fn __reduce__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        // frob:todo T-0010
        // Cache typani.result._rebuild_err in a
        // PyOnceLock (like UNWRAP_ERROR above) instead of a fresh
        // module import + getattr on every pickle; deferred since pickling
        // is not the hot path this ticket optimizes for (see
        // docs/native.md's benchmark table).
        let rebuild = py.import("typani.result")?.getattr("_rebuild_err")?;
        let args = (
            self.error.bind(py),
            self.notes.bind(py),
            self.trace.bind(py),
        );
        (rebuild, args).into_py_any(py)
    }

    fn __copy__(self_: &Bound<'_, Self>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn __deepcopy__(&self, py: Python<'_>, memo: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let copy_mod = py.import("copy")?;
        let deep = copy_mod.getattr(intern!(py, "deepcopy"))?;
        let copied = deep.call1((self.error.bind(py), memo))?;
        make_err_traced(
            py,
            copied,
            self.notes.clone_ref(py),
            self.trace.clone_ref(py),
        )
    }
}

impl ErrClass {
    /// Append `"; note: ..."` segments for each attached note (matches
    /// `Err._render_notes` in the pure-Python implementation).
    fn render_notes(&self, py: Python<'_>, base: String) -> String {
        let notes = self.notes.bind(py);
        let trace = self.trace.bind(py);
        if notes.is_empty() && trace.is_empty() {
            return base;
        }
        let mut out = base;
        out.pop(); // drop trailing ')'
        for note in notes.iter() {
            out.push_str("; note: ");
            out.push_str(&note.str().map(|s| s.to_string()).unwrap_or_default());
        }
        if !trace.is_empty() {
            out.push_str("; via ");
            let sites: Vec<String> = trace
                .iter()
                .map(|site| site.str().map(|s| s.to_string()).unwrap_or_default())
                .collect();
            out.push_str(&sites.join(" <- "));
        }
        out.push(')');
        out
    }
}

/// BIND: register(py, m) -> registers Result, Ok, Err on the module
///
/// WHY: `Err::__reduce__` calls `typani.result._rebuild_err` by name
/// (defined in Python, src/typani/result.py) rather than defining a
/// duplicate here, so both backends' `Err` pickles reconstruct through
/// one shared entry point.
pub(crate) fn register(py: Python<'_>, m: &Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    let _ = py;
    m.add_class::<ResultBase>()?;
    m.add_class::<OkClass>()?;
    m.add_class::<ErrClass>()?;
    Ok(())
}
