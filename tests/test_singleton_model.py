"""Tests for SingletonModel -- Pydantic BaseModel with singleton semantics."""

import pytest
from pydantic import Field, ValidationError

from typani.singleton import SingletonMeta, SingletonModel


class AppConfig(SingletonModel):
    debug: bool = False
    host: str = "localhost"
    port: int = 8080


class DatabaseConfig(SingletonModel):
    url: str = "sqlite:///db.sqlite3"
    pool_size: int = 5


def setup_function() -> None:
    SingletonMeta.instances.clear()


def test_same_instance_returned() -> None:
    cfg1 = AppConfig(debug=True)
    cfg2 = AppConfig()
    assert cfg1 is cfg2


def test_first_call_values_are_kept() -> None:
    AppConfig(debug=True, host="example.com", port=9000)
    cfg2 = AppConfig()
    assert cfg2.debug is True
    assert cfg2.host == "example.com"
    assert cfg2.port == 9000


def test_different_subclasses_are_independent() -> None:
    app = AppConfig(debug=True)
    db = DatabaseConfig(url="postgres://localhost/mydb")
    assert app is not db
    assert AppConfig() is app
    assert DatabaseConfig() is db


def test_pydantic_field_defaults() -> None:
    cfg = AppConfig()
    assert cfg.debug is False
    assert cfg.host == "localhost"
    assert cfg.port == 8080


def test_pydantic_validation_on_first_call() -> None:
    with pytest.raises(ValidationError):
        AppConfig(port="not-a-number")  # type: ignore[arg-type]


def test_field_descriptor_works() -> None:
    class Server(SingletonModel):
        host: str = Field(default="0.0.0.0", description="bind address")
        port: int = Field(default=8080, ge=1, le=65535)

    s = Server()
    assert s.host == "0.0.0.0"
    assert s.port == 8080


def test_is_pydantic_model() -> None:
    from pydantic import BaseModel

    assert issubclass(AppConfig, BaseModel)


def test_singleton_meta_is_in_mro() -> None:
    assert issubclass(type(AppConfig), SingletonMeta)
