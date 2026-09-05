from typani._exceptions import UnwrapError
from typani._impl import backend_name, native_active
from typani._propagate import catching, propagate
from typani._version import __version__
from typani.dispatch import dispatch
from typani.error_set import ErrorSet, merge
from typani.option import Nothing, Option, Some
from typani.result import Err, Ok, Result
from typani.singleton import (
    Singleton,
    SingletonMeta,
    SingletonModel,
    StrictSingleton,
    StrictSingletonMeta,
    singleton,
)
from typani.sum import Sum
from typani.unit import Unit
from typani.unreachable import Unreachable

__all__ = [
    "__version__",
    "backend_name",
    "native_active",
    "dispatch",
    "Sum",
    "ErrorSet",
    "merge",
    "Nothing",
    "Option",
    "Some",
    "Err",
    "Ok",
    "Result",
    "UnwrapError",
    "propagate",
    "catching",
    "singleton",
    "Singleton",
    "SingletonMeta",
    "SingletonModel",
    "StrictSingleton",
    "StrictSingletonMeta",
    "Unit",
    "Unreachable",
]
