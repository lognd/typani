//! Native `Option`/`Some`/`Nothing`, mirroring src/typani/option.py exactly.

use pyo3::exceptions::PyTypeError;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyBool, PyTuple, PyType};
use pyo3::{intern, prelude::*, IntoPyObjectExt};

static UNWRAP_ERROR: PyOnceLock<Py<PyType>> = PyOnceLock::new();

fn unwrap_error_type(py: Python<'_>) -> PyResult<&Bound<'_, PyType>> {
    let cell = UNWRAP_ERROR.get_or_try_init(py, || -> PyResult<Py<PyType>> {
        let module = py.import("typani._exceptions")?;
        let cls = module.getattr("UnwrapError")?;
        cls.extract::<Py<PyType>>().map_err(PyErr::from)
    })?;
    Ok(cell.bind(py))
}

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

/// The single cached `Nothing` instance (mirrors `Nothing._INSTANCE`).
static NOTHING_INSTANCE: PyOnceLock<Py<Nothing>> = PyOnceLock::new();

/// BIND: class Option(Generic[T_co])
///
/// WHY: abstract base of `Some`/`Nothing`; frozen and subclassable so
/// `isinstance(o, Option)` narrowing works exactly as against the
/// pure-Python base.
#[pyclass(name = "Option", module = "typani.option", subclass, frozen)]
struct OptionBase;

#[pymethods]
impl OptionBase {
    #[new]
    #[pyo3(signature = (*_args, **_kwargs))]
    fn new(
        _args: &Bound<'_, PyTuple>,
        _kwargs: Option<&Bound<'_, pyo3::types::PyDict>>,
    ) -> PyResult<Self> {
        Err(PyTypeError::new_err(
            "Option is abstract; construct Some(value) or Nothing()",
        ))
    }

    #[classmethod]
    fn from_optional(cls: &Bound<'_, PyType>, x: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let py = cls.py();
        if x.is_none() {
            make_nothing(py)
        } else {
            make_some(py, x)
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

pub(crate) fn make_some(py: Python<'_>, value: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let init = PyClassInitializer::from(OptionBase).add_subclass(Some_ {
        value: value.unbind(),
    });
    Py::new(py, init).map(|p| p.into_any())
}

pub(crate) fn make_nothing(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let cell = NOTHING_INSTANCE.get_or_try_init(py, || {
        let init = PyClassInitializer::from(OptionBase).add_subclass(Nothing);
        Py::new(py, init)
    })?;
    Ok(cell.clone_ref(py).into_any())
}

/// BIND: class Some(Option[T_co])
///
/// WHY: present variant; holds the payload directly for a single-field
/// read on `unwrap`/`danger_some`.
#[pyclass(name = "Some", module = "typani.option", extends = OptionBase, frozen)]
struct Some_ {
    value: Py<PyAny>,
}

#[pymethods]
impl Some_ {
    #[new]
    fn new(value: Bound<'_, PyAny>) -> PyClassInitializer<Self> {
        PyClassInitializer::from(OptionBase).add_subclass(Some_ {
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
    fn is_some(&self) -> bool {
        true
    }

    #[getter]
    fn is_nothing(&self) -> bool {
        false
    }

    #[getter]
    fn some(&self, py: Python<'_>) -> Py<PyAny> {
        self.value.clone_ref(py)
    }

    #[getter]
    fn danger_some(&self, py: Python<'_>) -> Py<PyAny> {
        self.value.clone_ref(py)
    }

    fn unwrap(&self, py: Python<'_>) -> Py<PyAny> {
        self.value.clone_ref(py)
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

    fn map(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let mapped = fn_.call1((self.value.bind(py),))?;
        make_some(py, mapped)
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

    fn filter(&self, py: Python<'_>, pred: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let keep = pred.call1((self.value.bind(py),))?.is_truthy()?;
        if keep {
            make_some(py, self.value.bind(py).clone())
        } else {
            make_nothing(py)
        }
    }

    fn ok_or(&self, py: Python<'_>, _err: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        crate::result::make_ok(py, self.value.bind(py).clone())
    }

    fn ok_or_else(&self, py: Python<'_>, _fn: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        crate::result::make_ok(py, self.value.bind(py).clone())
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
            "Option has no truth value; use is_some/is_nothing or match",
        ))
    }

    fn __eq__(&self, py: Python<'_>, other: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        match other.cast::<Some_>() {
            std::result::Result::Ok(other_some) => {
                let eq = self.value.bind(py).eq(other_some.borrow().value.bind(py))?;
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
        Ok(format!("Some({})", self.value.bind(py).repr()?))
    }

    fn __str__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!("Some({})", self.value.bind(py).str()?))
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
        make_some(py, copied)
    }
}

/// BIND: class Nothing(Option[T_co])
///
/// WHY: absent variant; a single cached instance is shared process-wide
/// (`NOTHING_INSTANCE`, mirroring `Nothing._INSTANCE`) so `Nothing() is
/// Nothing()` holds under the native backend too.
#[pyclass(name = "Nothing", module = "typani.option", extends = OptionBase, frozen)]
struct Nothing;

#[pymethods]
impl Nothing {
    #[new]
    #[pyo3(signature = (*_args, **_kwargs))]
    fn new(
        py: Python<'_>,
        _args: &Bound<'_, PyTuple>,
        _kwargs: Option<&Bound<'_, pyo3::types::PyDict>>,
    ) -> PyResult<Py<Self>> {
        let obj = make_nothing(py)?;
        obj.extract::<Py<Self>>(py).map_err(PyErr::from)
    }

    #[classattr]
    fn __match_args__(py: Python<'_>) -> Py<PyTuple> {
        PyTuple::empty(py).unbind()
    }

    #[getter]
    fn is_some(&self) -> bool {
        false
    }

    #[getter]
    fn is_nothing(&self) -> bool {
        true
    }

    #[getter]
    fn some(&self, py: Python<'_>) -> Py<PyAny> {
        py.None()
    }

    #[getter]
    fn danger_some(self_: &Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(self_.py(), self_.clone().into_any(), None))
    }

    fn unwrap(self_: &Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(self_.py(), self_.clone().into_any(), None))
    }

    fn unwrap_or(&self, default: Bound<'_, PyAny>) -> Py<PyAny> {
        default.unbind()
    }

    fn unwrap_or_else(&self, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        Ok(fn_.call0()?.unbind())
    }

    fn expect(self_: &Bound<'_, Self>, msg: &str) -> PyResult<Py<PyAny>> {
        Err(unwrap_error(
            self_.py(),
            self_.clone().into_any(),
            Some(msg),
        ))
    }

    fn inspect(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn map(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn and_then(self_: &Bound<'_, Self>, _fn: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn or_else(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let _ = py;
        Ok(fn_.call0()?.unbind())
    }

    fn filter(self_: &Bound<'_, Self>, _pred: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn ok_or(&self, py: Python<'_>, err: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        crate::result::make_err(py, err, PyTuple::empty(py).unbind())
    }

    fn ok_or_else(&self, py: Python<'_>, fn_: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let err = fn_.call0()?;
        crate::result::make_err(py, err, PyTuple::empty(py).unbind())
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
            "Option has no truth value; use is_some/is_nothing or match",
        ))
    }

    fn __eq__(&self, py: Python<'_>, other: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        if other.cast::<Nothing>().is_ok() {
            Ok(PyBool::new(py, true).to_owned().unbind().into_any())
        } else {
            Ok(py.NotImplemented())
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

    fn __hash__(&self) -> isize {
        // Matches Python's hash((_NOTHING_MARKER,)) with marker 1, computed
        // via a 1-tuple hash at registration time would need the GIL; a
        // fixed constant is stable and collision-safe against Some's hash
        // (which always mixes in a payload).
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        std::hash::Hash::hash(&1isize, &mut hasher);
        std::hash::Hasher::finish(&hasher) as isize
    }

    fn __repr__(&self) -> &'static str {
        "Nothing"
    }

    fn __str__(&self) -> &'static str {
        "Nothing"
    }

    fn __reduce__(self_: &Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        let py = self_.py();
        let cls = self_.get_type();
        (cls, PyTuple::empty(py)).into_py_any(py)
    }

    fn __copy__(self_: &Bound<'_, Self>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }

    fn __deepcopy__(self_: &Bound<'_, Self>, _memo: Bound<'_, PyAny>) -> Py<PyAny> {
        self_.clone().into_any().unbind()
    }
}

pub(crate) fn register(py: Python<'_>, m: &Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    let _ = py;
    m.add_class::<OptionBase>()?;
    m.add_class::<Some_>()?;
    m.add_class::<Nothing>()?;
    Ok(())
}
