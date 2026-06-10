"""Tests for operator aliases on Result and Option."""

from typani.option import Nothing, Option, Some
from typani.result import Err, Ok, Result


class TestResultPipe:
    def test_pipe_maps_ok(self) -> None:
        result: Result[int, str] = Ok(5) | (lambda x: x * 2)
        assert result.ok == 10

    def test_pipe_passes_err_through(self) -> None:
        result: Result[int, str] = Err("bad") | (lambda x: x * 2)
        assert result.err == "bad"

    def test_rshift_chains_ok(self) -> None:
        result: Result[int, str] = Ok(3) >> (lambda x: Ok(x + 1))
        assert result.ok == 4

    def test_rshift_propagates_first_err(self) -> None:
        result: Result[int, str] = Err("first") >> (lambda x: Ok(x + 1))
        assert result.err == "first"

    def test_rshift_propagates_inner_err(self) -> None:
        result: Result[int, str] = Ok(1) >> (lambda _: Err("inner"))
        assert result.err == "inner"

    def test_chained_pipes(self) -> None:
        result = Ok(1) | (lambda x: x + 1) | (lambda x: x * 3)
        assert result.ok == 6

    def test_chained_rshifts(self) -> None:
        result = Ok(2) >> (lambda x: Ok(x + 1)) >> (lambda x: Ok(x * 4))
        assert result.ok == 12


class TestOptionPipe:
    def test_pipe_maps_some(self) -> None:
        result: Option[int] = Some(4) | (lambda x: x + 1)
        assert result.some == 5

    def test_pipe_passes_nothing_through(self) -> None:
        result: Option[int] = Nothing() | (lambda x: x + 1)
        assert result.is_nothing

    def test_rshift_chains_some(self) -> None:
        result: Option[int] = Some(3) >> (lambda x: Some(x * 2))
        assert result.some == 6

    def test_rshift_propagates_nothing(self) -> None:
        result: Option[int] = Nothing() >> (lambda x: Some(x * 2))
        assert result.is_nothing

    def test_rshift_inner_nothing(self) -> None:
        result: Option[int] = Some(1) >> (lambda _: Nothing())
        assert result.is_nothing

    def test_chained_pipes(self) -> None:
        result = Some(10) | (lambda x: x - 3) | (lambda x: x * 2)
        assert result.some == 14
