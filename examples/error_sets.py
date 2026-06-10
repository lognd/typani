"""
ErrorSet example.

Shows how to define per-domain error sets, merge them into a single app-level
set, and use them as Result error types with rich descriptions.
"""

from __future__ import annotations

import random

from typani import Err, ErrorSet, Ok, Result


# ---------------------------------------------------------------------------
# Per-domain error sets
# ---------------------------------------------------------------------------


class NetworkError(ErrorSet):
    Timeout    = "connection timed out after the deadline"
    Refused    = "remote host actively refused the connection"
    DnsFailure = "could not resolve the hostname"


class ParseError(ErrorSet):
    InvalidJson = "payload is not valid JSON"
    MissingKey  = "required key not present in the payload"
    BadType     = "field value has an unexpected type"


class AuthError(ErrorSet):
    Unauthorized = "request lacks valid authentication credentials"
    Forbidden    = "authenticated user lacks permission for this resource"
    TokenExpired = "authentication token has expired"


# Combine into one app-level set with | -- like Zig's || operator.
# A | B | C is cached and commutative: any ordering returns the same object.
AppError = NetworkError | ParseError | AuthError


# ---------------------------------------------------------------------------
# Functions that return typed errors
# ---------------------------------------------------------------------------


def fetch_raw(url: str) -> Result[str, NetworkError]:
    """Simulate an HTTP fetch that can fail with a NetworkError."""
    outcome = random.choice(["ok", "timeout", "refused"])
    if outcome == "timeout":
        return Err(NetworkError.Timeout)
    if outcome == "refused":
        return Err(NetworkError.Refused)
    return Ok('{"user": "alice", "role": "admin"}')


def parse_user(payload: str) -> Result[dict, ParseError]:
    """Simulate JSON parsing that can fail with a ParseError."""
    import json
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return Err(ParseError.InvalidJson)
    if "user" not in data:
        return Err(ParseError.MissingKey)
    return Ok(data)


def check_auth(data: dict) -> Result[dict, AuthError]:
    """Simulate an auth check that can fail with an AuthError."""
    if data.get("role") != "admin":
        return Err(AuthError.Forbidden)
    return Ok(data)


# ---------------------------------------------------------------------------
# Pipeline that can produce any of the three error types
# ---------------------------------------------------------------------------


def get_admin_user(url: str) -> Result[dict, AppError]:
    """
    Chain fetch -> parse -> auth.  The error type widens at each step.
    All three error kinds are visible in the return type.
    """
    raw = fetch_raw(url)
    if raw.is_err:
        return Err(AppError[raw.danger_err.name])   # re-wrap into the merged set

    parsed = parse_user(raw.danger_ok)
    if parsed.is_err:
        return Err(AppError[parsed.danger_err.name])

    return check_auth(parsed.danger_ok)  # type: ignore[return-value]


def main() -> None:
    # Show all member descriptions
    print("=== AppError members ===")
    for member in AppError:
        print(f"  {repr(member)}: {member.description}")

    print()

    # Run the pipeline a few times to hit different outcomes
    print("=== Pipeline runs ===")
    for _ in range(6):
        result = get_admin_user("https://api.example.com/me")
        if result.is_ok:
            print(f"  OK -> {result.ok}")
        else:
            err = result.danger_err
            print(f"  ERR -> {err}  (description: {err.description!r})")


if __name__ == "__main__":
    main()
