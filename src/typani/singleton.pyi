from typing import Any, TypeVar

import pydantic

T = TypeVar("T")


class SingletonMeta(type):
    instances: dict[type, object]
    def __call__(cls, *args: Any, **kwargs: Any) -> Any: ...


class StrictSingletonMeta(type):
    instances: dict[type, object]
    def __call__(cls, *args: Any, **kwargs: Any) -> Any: ...


class Singleton(metaclass=SingletonMeta): ...


class StrictSingleton(metaclass=StrictSingletonMeta):
    @classmethod
    def instance(cls: type[T]) -> T: ...


def singleton(cls: type[T] | None = ..., *, strict: bool = ...) -> Any: ...


class SingletonModel(pydantic.BaseModel):
    """Pydantic BaseModel subclass that enforces the singleton pattern."""
    ...
