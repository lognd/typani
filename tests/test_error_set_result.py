"""Integration tests: ErrorSet used as the error type in Result."""

from typani import Err, ErrorSet, Ok, Result, merge


class NetworkError(ErrorSet):
    Timeout = "connection timed out"
    Refused = "connection refused"
    DnsFailure = "could not resolve hostname"


class ParseError(ErrorSet):
    InvalidJson = "payload is not valid JSON"
    MissingKey = "required key not present"


AppError = merge(NetworkError, ParseError, name="AppError")


# ---------------------------------------------------------------------------
# Basic construction
# ---------------------------------------------------------------------------


# frob:tests src/typani/error_set.py kind="integration"
def test_ok_with_error_set_type() -> None:
    r: Result[str, NetworkError] = Ok("connected")
    assert r.is_ok
    assert r.ok == "connected"


# frob:tests src/typani/result.py kind="integration"
def test_err_with_error_set_member() -> None:
    r: Result[str, NetworkError] = Err(NetworkError.Timeout)
    assert r.is_err
    assert r.err is NetworkError.Timeout


def test_err_description_accessible() -> None:
    r: Result[str, NetworkError] = Err(NetworkError.Refused)
    assert r.danger_err.description == "connection refused"


# ---------------------------------------------------------------------------
# map / map_err / and_then
# ---------------------------------------------------------------------------


def test_map_on_ok_does_not_affect_error_type() -> None:
    r: Result[int, NetworkError] = Ok(3)
    mapped = r.map(lambda x: x * 2)
    assert mapped.ok == 6


def test_map_err_transforms_description() -> None:
    r: Result[str, NetworkError] = Err(NetworkError.DnsFailure)
    upper = r.map_err(lambda e: e.description.upper())
    assert upper.err == "COULD NOT RESOLVE HOSTNAME"


def test_and_then_propagates_error_set_err() -> None:
    def validate(s: str) -> Result[str, ParseError]:
        if not s:
            return Err(ParseError.MissingKey)
        return Ok(s)

    r: Result[str, NetworkError] = Err(NetworkError.Timeout)
    chained = r.and_then(validate)
    assert chained.is_err
    assert chained.err is NetworkError.Timeout


def test_and_then_returns_inner_error_set_err() -> None:
    def validate(s: str) -> Result[str, ParseError]:
        return Err(ParseError.InvalidJson)

    r: Result[str, NetworkError] = Ok("data")
    chained = r.and_then(validate)
    assert chained.is_err
    assert chained.err is ParseError.InvalidJson


# ---------------------------------------------------------------------------
# Operator shortcuts
# ---------------------------------------------------------------------------


def test_pipe_operator_on_ok() -> None:
    r: Result[str, NetworkError] = Ok("hello")
    result = r | str.upper
    assert result.ok == "HELLO"


def test_pipe_operator_passes_through_err() -> None:
    r: Result[str, NetworkError] = Err(NetworkError.Timeout)
    result = r | str.upper
    assert result.is_err
    assert result.err is NetworkError.Timeout


def test_rshift_operator_chains_ok() -> None:
    def parse(s: str) -> Result[int, ParseError]:
        return Ok(len(s))

    r: Result[str, NetworkError] = Ok("hello")
    result = r >> parse
    assert result.ok == 5


def test_rshift_operator_short_circuits_on_err() -> None:
    called = []

    def parse(s: str) -> Result[int, ParseError]:
        called.append(s)
        return Ok(len(s))

    r: Result[str, NetworkError] = Err(NetworkError.Refused)
    result = r >> parse
    assert result.is_err
    assert not called


# ---------------------------------------------------------------------------
# Merged error set as Result error type
# ---------------------------------------------------------------------------


def test_merged_set_as_result_error_type() -> None:
    r: Result[str, AppError] = Err(AppError.Timeout)
    assert r.is_err
    assert r.danger_err.description == "connection timed out"


def test_merged_set_contains_all_members() -> None:
    names = {m.name for m in AppError}
    assert "Timeout" in names
    assert "InvalidJson" in names


def test_pipe_on_ok_with_merged_error_type() -> None:
    r: Result[str, AppError] = Ok("payload")
    result = r | (lambda s: s.upper())
    assert result.ok == "PAYLOAD"


# ---------------------------------------------------------------------------
# __class_getitem__ / union annotation compatibility
# ---------------------------------------------------------------------------


def test_result_class_getitem_with_error_set() -> None:
    # Result[str, NetworkError] must not raise at subscription time
    alias = Result[str, NetworkError]
    assert alias is not None


def test_int_or_error_set_is_union_type() -> None:
    import types

    union = int | NetworkError
    assert isinstance(union, types.UnionType)


def test_error_set_or_error_set_is_merged_set() -> None:
    merged = NetworkError | ParseError
    assert issubclass(merged, ErrorSet)
    names = {m.name for m in merged}
    assert "Timeout" in names
    assert "InvalidJson" in names


def test_error_set_or_non_error_set_falls_back_to_union() -> None:
    import types

    union = NetworkError | str
    assert isinstance(union, types.UnionType)
