"""Tests for the @singleton decorator and StrictSingleton."""

import pytest
from pydantic import BaseModel, Field, ValidationError

from typani.singleton import (
    SingletonMeta,
    StrictSingleton,
    StrictSingletonMeta,
    singleton,
)

# ---------------------------------------------------------------------------
# Helpers -- reset singleton state between tests
# ---------------------------------------------------------------------------


def setup_function() -> None:
    SingletonMeta.instances.clear()
    StrictSingletonMeta.instances.clear()


# ---------------------------------------------------------------------------
# @singleton -- regular classes
# ---------------------------------------------------------------------------


def test_decorator_returns_same_instance() -> None:
    @singleton
    class Service:
        def __init__(self, x: int = 0) -> None:
            self.x = x

    a = Service(x=1)
    b = Service(x=99)
    assert a is b
    assert a.x == 1


def test_decorator_preserves_name() -> None:
    @singleton
    class MyService:
        pass

    assert MyService.__name__ == "MyService"


def test_decorator_preserves_isinstance() -> None:
    class Base:
        pass

    @singleton
    class Child(Base):
        pass

    assert isinstance(Child(), Base)


def test_decorator_independent_classes() -> None:
    @singleton
    class A:
        pass

    @singleton
    class B:
        pass

    assert A() is not B()
    assert A() is A()
    assert B() is B()


def test_decorator_idempotent_on_singleton_subclass() -> None:
    from typani.singleton import Singleton

    @singleton
    class Already(Singleton):
        pass

    a = Already()
    b = Already()
    assert a is b


# ---------------------------------------------------------------------------
# @singleton -- Pydantic models
# ---------------------------------------------------------------------------


def test_decorator_pydantic_same_instance() -> None:
    @singleton
    class Config(BaseModel):
        debug: bool = False
        host: str = "localhost"

    a = Config(debug=True, host="prod")
    b = Config(debug=False, host="dev")
    assert a is b
    assert a.debug is True
    assert a.host == "prod"


def test_decorator_pydantic_defaults() -> None:
    @singleton
    class Config(BaseModel):
        port: int = 8080

    c = Config()
    assert c.port == 8080


def test_decorator_pydantic_field_validation() -> None:
    @singleton
    class Config(BaseModel):
        port: int = Field(ge=1, le=65535, default=8080)

    with pytest.raises(ValidationError):
        Config(port=99999)


def test_decorator_pydantic_is_base_model() -> None:
    @singleton
    class Config(BaseModel):
        x: int = 0

    assert isinstance(Config(), BaseModel)


# ---------------------------------------------------------------------------
# @singleton(strict=True) -- decorator with parameter
# ---------------------------------------------------------------------------


def test_strict_decorator_first_call_ok() -> None:
    @singleton(strict=True)
    class DB:
        def __init__(self, url: str = "sqlite://") -> None:
            self.url = url

    d = DB(url="postgres://")
    assert d.url == "postgres://"


def test_strict_decorator_raises_on_second_call() -> None:
    @singleton(strict=True)
    class DB:
        pass

    DB()
    with pytest.raises(RuntimeError, match="strict singleton"):
        DB()


# ---------------------------------------------------------------------------
# StrictSingleton base class
# ---------------------------------------------------------------------------


def test_strict_singleton_first_call_ok() -> None:
    class Cache(StrictSingleton):
        def __init__(self, size: int = 128) -> None:
            self.size = size

    c = Cache(size=256)
    assert c.size == 256


def test_strict_singleton_raises_on_second_call() -> None:
    class Cache(StrictSingleton):
        pass

    Cache()
    with pytest.raises(RuntimeError, match="strict singleton"):
        Cache()


def test_strict_singleton_instance_classmethod() -> None:
    class Cache(StrictSingleton):
        def __init__(self) -> None:
            self.ready = True

    Cache()
    c = Cache.instance()
    assert c.ready is True


def test_strict_singleton_instance_before_creation_raises() -> None:
    class Fresh(StrictSingleton):
        pass

    with pytest.raises(LookupError, match="not been instantiated"):
        Fresh.instance()


def test_strict_singleton_independent_classes() -> None:
    class X(StrictSingleton):
        pass

    class Y(StrictSingleton):
        pass

    X()
    Y()
    with pytest.raises(RuntimeError):
        X()
    # Y is still in its own bucket -- this would also raise if called again
    assert X.instance() is not Y.instance()


def test_strict_singleton_meta_directly() -> None:
    class MyLock(metaclass=StrictSingletonMeta):
        pass

    MyLock()
    with pytest.raises(RuntimeError):
        MyLock()
