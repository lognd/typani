"""
Result + Option pipeline example.

Shows how Result and Option chain with | (map) and >> (and_then) to build
a multi-step data processing pipeline without any explicit error forwarding.
"""

from __future__ import annotations

import json
import os

from typani import Err, Nothing, Ok, Option, Result, Some, propagate

# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def read_env(key: str) -> Result[str, str]:
    """Read an environment variable or return a descriptive Err."""
    val = os.getenv(key)
    return Ok(val) if val is not None else Err(f"missing env var {key!r}")


def parse_json(text: str) -> Result[dict, str]:
    """Parse JSON text, returning Err on invalid input."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return Err(f"JSON parse error: {exc.msg}")
    if not isinstance(data, dict):
        return Err("expected a JSON object at the top level")
    return Ok(data)


def get_key(data: dict, key: str) -> Option[str]:
    """Extract a string field from a dict, returning Nothing if absent."""
    val = data.get(key)
    return Some(str(val)) if val is not None else Nothing()


# ---------------------------------------------------------------------------
# Composed pipeline
# ---------------------------------------------------------------------------


def load_server_config() -> Result[dict, str]:
    """
    Read $APP_CONFIG (JSON string), parse it, and return the config dict.

    Equivalent to:
        raw  = read_env("APP_CONFIG")
        if raw.is_err: return raw
        data = parse_json(raw.ok)
        return data

    Written as a pipeline instead.
    """
    return read_env("APP_CONFIG") >> parse_json


@propagate
def load_server_host() -> Result[str, str]:
    """
    Read+parse the config, then pull out its "host" field.

    ``@propagate`` turns ``.unwrap()`` on a failing ``Result``/``Option``
    into an early return of that same container -- Rust ``?`` / Zig ``try``
    style -- instead of hand-written ``if r.is_err: return Err(r.danger_err)``
    at each step. ``.note(...)`` attaches context to a still-failing ``Err``
    without touching its payload.
    """
    data = load_server_config().note("while loading server host").unwrap()
    return Ok(get_key(data, "host").expect("config has no 'host' field"))


def main() -> None:
    # --- Happy path ---
    os.environ["APP_CONFIG"] = '{"host": "prod.example.com", "port": 9000}'
    cfg = load_server_config()
    match cfg:
        case Ok(value):
            print("config loaded:", value)
        case Err(error):
            print("config load failed:", error)

    # Extract an optional field from the parsed config
    host: Option[str] = get_key(cfg.danger_ok, "host")
    display = host | str.upper | (lambda s: f"[{s}]")
    print("host display:", display.unwrap_or("unknown"))

    # Same field, via the @propagate-based pipeline above
    print("host (propagate):", load_server_host().unwrap())

    # --- Missing env var ---
    del os.environ["APP_CONFIG"]
    missing = load_server_config()
    match missing:
        case Ok(_):
            raise AssertionError("expected an Err for a missing env var")
        case Err(error):
            print("missing env:", error)

    # --- Bad JSON ---
    os.environ["APP_CONFIG"] = "not json"
    bad = load_server_config()
    match bad:
        case Ok(_):
            raise AssertionError("expected an Err for invalid JSON")
        case Err(error):
            print("bad json:", error)


if __name__ == "__main__":
    main()
