"""
Singleton example.

Shows Singleton base class, @singleton decorator on a plain class and on a
Pydantic model, and StrictSingleton for catching accidental double-init.
"""

from __future__ import annotations

from typani import Singleton, StrictSingleton, singleton

# ---------------------------------------------------------------------------
# Basic Singleton base class
# ---------------------------------------------------------------------------


class AppSettings(Singleton):
    """Application-wide settings.  Constructed once; shared everywhere."""

    def __init__(self, debug: bool = False, log_level: str = "INFO") -> None:
        self.debug = debug
        self.log_level = log_level


# First call constructs
settings = AppSettings(debug=True, log_level="DEBUG")

# Every subsequent call returns the same object
also_settings = AppSettings(debug=False, log_level="WARNING")
assert settings is also_settings
assert settings.debug is True  # first-call values are kept
print(f"settings: debug={settings.debug}, log_level={settings.log_level}")


# ---------------------------------------------------------------------------
# @singleton decorator -- no base-class change needed
# ---------------------------------------------------------------------------


@singleton
class Cache:
    """In-memory cache.  Shared singleton -- no subclassing required."""

    def __init__(self, max_size: int = 256) -> None:
        self.max_size = max_size
        self._store: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        self._store[key] = value

    def get(self, key: str) -> object | None:
        return self._store.get(key)


cache_a = Cache(max_size=1024)
cache_b = Cache()  # returns same object
assert cache_a is cache_b
assert cache_a.max_size == 1024

cache_a.set("greeting", "hello")
print(f"cache get: {cache_b.get('greeting')}")  # "hello" via the shared instance


# ---------------------------------------------------------------------------
# @singleton with Pydantic
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel, Field

    @singleton
    class ServerConfig(BaseModel):
        host: str = "localhost"
        port: int = Field(default=8080, ge=1, le=65535)
        workers: int = 4

    cfg1 = ServerConfig(host="prod.example.com", port=9000, workers=8)
    cfg2 = ServerConfig(host="ignored", port=80)  # returns same object
    assert cfg1 is cfg2
    assert cfg2.host == "prod.example.com"
    print(f"server config: host={cfg1.host}, port={cfg1.port}, workers={cfg1.workers}")

except ImportError:
    print("pydantic not installed -- skipping ServerConfig example")


# ---------------------------------------------------------------------------
# StrictSingleton -- raises on second instantiation
# ---------------------------------------------------------------------------


class DatabaseConnection(StrictSingleton):
    """
    Represents the single live database connection.
    Accidental second instantiation is a bug -- make it loud.
    """

    def __init__(self, url: str) -> None:
        self.url = url
        print(f"DatabaseConnection opened: {self.url}")

    def query(self, sql: str) -> str:
        return f"[{self.url}] -> {sql}"


db = DatabaseConnection("postgres://localhost/mydb")
print(db.query("SELECT 1"))

# Retrieve the same instance without going through the constructor
same_db = DatabaseConnection.instance()
assert same_db is db

# Second instantiation raises immediately
try:
    DatabaseConnection("sqlite://")
except RuntimeError as exc:
    print(f"Caught expected error: {exc}")
