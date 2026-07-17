import pytest

from typani.error_set import ErrorSet, merge
from typani.result import Err, Ok, Result


class NetworkError(ErrorSet):
    Timeout = "Connection timed out after the deadline"
    Refused = "Remote host actively refused the connection"


class ParseError(ErrorSet):
    InvalidJson = "Input is not valid JSON"
    UnexpectedEof = "Unexpected end of input"


class AuthError(ErrorSet):
    Unauthorized = "Missing or invalid credentials"


# frob:tests src/typani/error_set.py::ErrorSet
def test_member_description() -> None:
    assert NetworkError.Timeout.description == "Connection timed out after the deadline"
    assert (
        NetworkError.Refused.description
        == "Remote host actively refused the connection"
    )


def test_str_format() -> None:
    assert (
        str(NetworkError.Timeout) == "Timeout: Connection timed out after the deadline"
    )


def test_repr_format() -> None:
    assert repr(NetworkError.Refused) == "NetworkError.Refused"


def test_members_are_distinct() -> None:
    assert NetworkError.Timeout is not NetworkError.Refused


def test_identity_equality() -> None:
    assert NetworkError.Timeout is NetworkError.Timeout


def test_different_sets_are_independent() -> None:
    assert NetworkError.Timeout != ParseError.InvalidJson  # type: ignore[comparison-overlap]


def test_used_as_result_error() -> None:
    def fetch(fail: bool) -> Result[str, NetworkError]:
        if fail:
            return Err(NetworkError.Timeout)
        return Ok("data")

    success = fetch(False)
    assert success.ok == "data"

    failure = fetch(True)
    assert failure.err is NetworkError.Timeout
    assert failure.err.description == "Connection timed out after the deadline"


def test_iteration_over_members() -> None:
    members = list(NetworkError)
    assert NetworkError.Timeout in members
    assert NetworkError.Refused in members
    assert len(members) == 2


# --- merge / global error set ---


# frob:tests src/typani/error_set.py::merge
def test_merge_combines_members() -> None:
    All = merge(NetworkError, ParseError, name="AllErrors")
    names = {m.name for m in All}
    assert names == {"Timeout", "Refused", "InvalidJson", "UnexpectedEof"}


def test_merge_preserves_descriptions() -> None:
    All = merge(NetworkError, ParseError)
    assert All["Timeout"].description == "Connection timed out after the deadline"
    assert All["InvalidJson"].description == "Input is not valid JSON"


def test_merge_three_sets() -> None:
    All = merge(NetworkError, ParseError, AuthError)
    assert len(list(All)) == 5


def test_merge_raises_on_duplicate_name() -> None:
    class Dup(ErrorSet):
        Timeout = "Another timeout description"

    with pytest.raises(ValueError, match="duplicate"):
        merge(NetworkError, Dup)


def test_pipe_operator_merges() -> None:
    All = NetworkError | ParseError  # type: ignore[operator]
    names = {m.name for m in All}
    assert "Timeout" in names
    assert "InvalidJson" in names


def test_pipe_operator_three_way() -> None:
    All = NetworkError | ParseError | AuthError  # type: ignore[operator]
    assert len(list(All)) == 5
