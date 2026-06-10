from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, overload

T = TypeVar("T")


class SingletonMeta(type):
    """Metaclass that ensures at most one instance is ever created per class.

    Subsequent constructor calls return the original instance rather than
    creating a new one.  Each distinct class gets its own slot in the shared
    instance registry, so ``A()`` and ``B()`` are independent even when both
    inherit from :class:`Singleton`.
    """

    instances: dict[type, object] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Return the cached instance, creating it on the first call."""
        if cls not in SingletonMeta.instances:
            SingletonMeta.instances[cls] = super().__call__(*args, **kwargs)
        return SingletonMeta.instances[cls]


class StrictSingletonMeta(type):
    """Metaclass that raises ``RuntimeError`` on any second instantiation attempt.

    Unlike :class:`SingletonMeta`, which silently returns the cached instance,
    ``StrictSingletonMeta`` enforces that the constructor is only ever called
    once.  This makes accidental double-instantiation a loud, visible failure
    rather than a silent no-op.
    """

    instances: dict[type, object] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Construct the first instance; raise on any subsequent call."""
        if cls in StrictSingletonMeta.instances:
            raise RuntimeError(
                f"{cls.__name__} is a strict singleton and has already been "
                f"instantiated.  Retrieve the existing instance via "
                f"{cls.__name__}.instance()."
            )
        instance = super().__call__(*args, **kwargs)
        StrictSingletonMeta.instances[cls] = instance
        return instance


class Singleton(metaclass=SingletonMeta):
    """Convenience base class for singletons.

    Subclasses are guaranteed to have at most one instance.  Subsequent
    constructor calls return the original instance silently::

        class AppConfig(Singleton):
            def __init__(self) -> None:
                self.debug = False

        cfg1 = AppConfig()
        cfg2 = AppConfig()
        assert cfg1 is cfg2  # True

    If you cannot inherit from ``Singleton`` (e.g. you already have another
    base with an incompatible metaclass), use the :func:`singleton` decorator
    instead -- it works with any class including Pydantic ``BaseModel``::

        @singleton
        class AppConfig(BaseModel):
            debug: bool = False
    """

    ...


class StrictSingleton(metaclass=StrictSingletonMeta):
    """Base class for strict singletons that raise on second instantiation.

    Unlike :class:`Singleton`, which silently returns the cached instance,
    ``StrictSingleton`` raises ``RuntimeError`` if the constructor is called
    more than once.  Use this when double-instantiation indicates a bug and
    you want it to surface immediately::

        class Database(StrictSingleton):
            def __init__(self, url: str) -> None:
                self.url = url

        db = Database("postgres://...")   # OK
        db2 = Database("sqlite://...")    # RuntimeError!

    Retrieve the existing instance via :meth:`instance`::

        Database.instance()  # returns the one created instance
    """

    @classmethod
    def instance(cls: type[T]) -> T:
        """Return the single instance; raises ``LookupError`` if not yet created."""
        inst = StrictSingletonMeta.instances.get(cls)
        if inst is None:
            raise LookupError(f"{cls.__name__} has not been instantiated yet.")
        return inst  # type: ignore[return-value]


@overload
def singleton(cls: type[T]) -> type[T]: ...


@overload
def singleton(*, strict: bool) -> Any: ...


def singleton(cls: type[T] | None = None, *, strict: bool = False) -> Any:
    """Decorator that makes any class a singleton -- including Pydantic BaseModels.

    Works by dynamically creating a merged metaclass from :class:`SingletonMeta`
    (or :class:`StrictSingletonMeta`) and the class's own metaclass, so the
    singleton semantics are enforced at the ``__call__`` level regardless of
    what base classes are involved.

    Usage::

        @singleton
        class AppConfig:
            def __init__(self, debug: bool = False) -> None:
                self.debug = debug

        @singleton
        class AppConfig(BaseModel):   # Pydantic works too
            debug: bool = False

        @singleton(strict=True)
        class Database:
            def __init__(self, url: str) -> None:
                self.url = url

    The returned class is a thin subclass of the original, so ``isinstance``
    checks, ``__name__``, and ``__module__`` are all preserved.

    *strict=True* uses :class:`StrictSingletonMeta` instead of
    :class:`SingletonMeta`: subsequent instantiation attempts raise
    ``RuntimeError`` rather than returning the cached instance.
    """

    def _apply(klass: type[T]) -> type[T]:
        base_meta = SingletonMeta if not strict else StrictSingletonMeta
        meta = type(klass)

        if issubclass(meta, base_meta):
            return klass  # already has singleton semantics via this meta

        if issubclass(base_meta, meta):
            merged = base_meta
        else:
            merged = type(f"_S{meta.__name__}", (base_meta, meta), {})

        new_cls: type[T] = merged(
            klass.__name__,
            (klass,),
            {"__module__": klass.__module__, "__qualname__": klass.__qualname__},
        )
        return new_cls

    if cls is not None:
        return _apply(cls)
    return _apply


def _make_singleton_model() -> type | None:
    """Return SingletonModel if pydantic is installed, else None."""
    try:
        from pydantic import BaseModel

        ModelMetaclass = type(BaseModel)

        class _SingletonModelMeta(SingletonMeta, ModelMetaclass):  # type: ignore[valid-type]
            """Merged metaclass: SingletonMeta + Pydantic model construction."""

        class _SingletonModel(BaseModel, metaclass=_SingletonModelMeta):
            """Pydantic ``BaseModel`` subclass that enforces the singleton pattern.

            Exactly one instance is created per subclass.  Subsequent constructor
            calls -- even with different field values -- return the original
            instance::

                from typani.singleton import SingletonModel
                from pydantic import Field

                class AppConfig(SingletonModel):
                    debug: bool = False
                    host: str = "localhost"
                    port: int = 8080

                cfg1 = AppConfig(debug=True)
                cfg2 = AppConfig()        # returns the same object
                assert cfg1 is cfg2       # True
                assert cfg2.debug         # True -- first call's values are kept

            Field validation, defaults, and all other Pydantic features work
            normally on the first construction.  Pydantic v2 (>=2.0) is required.

            Prefer the :func:`singleton` decorator if you want the normal
            ``class Cfg(BaseModel): ...`` declaration style.
            """

            model_config = {"arbitrary_types_allowed": True}

        return _SingletonModel
    except ImportError:
        return None


_singleton_model = _make_singleton_model()

if TYPE_CHECKING:
    import pydantic

    class SingletonModel(pydantic.BaseModel):
        """Pydantic ``BaseModel`` subclass that enforces the singleton pattern.

        Exactly one instance is created per subclass.  Subsequent constructor
        calls return the original instance::

            class AppConfig(SingletonModel):
                debug: bool = False
                host: str = "localhost"

            cfg1 = AppConfig(debug=True)
            cfg2 = AppConfig()
            assert cfg1 is cfg2    # True
            assert cfg2.debug      # True

        Requires pydantic>=2.0.  Prefer :func:`singleton` if you want the
        normal ``class Cfg(BaseModel): ...`` declaration style.
        """

        ...

else:
    if _singleton_model is not None:
        SingletonModel = _singleton_model
    else:

        class SingletonModel:  # type: ignore[no-redef]
            """Placeholder that raises ImportError when pydantic is not installed."""

            def __init_subclass__(cls, **kwargs: Any) -> None:
                raise ImportError(
                    "SingletonModel requires pydantic>=2.0. "
                    "Install it with: pip install pydantic"
                )
