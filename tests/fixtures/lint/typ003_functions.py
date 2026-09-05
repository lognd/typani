"""Fixture: TYP003 discarded-Result/Option across constructors, functions, chains."""

from __future__ import annotations


def helper() -> int:
    """Not Result/Option-returning; calling it as a statement is fine."""
    return 1


def make() -> "Result[int, str]":
    """Returns a Result; calling it as a bare statement should be flagged."""
    return Ok(1)


class Widget:
    """Fixture class exercising self.<method>() discard detection."""

    def method(self) -> "Result[int, str]":
        """Returns a Result via self; a bare self.method() call is flagged."""
        return Ok(1)

    def other(self) -> None:
        """Not Result/Option-returning; self.other() as a statement is fine."""
        return None

    def use(self) -> None:
        """Exercises both the flagged and the clean self-call shapes."""
        self.method()
        self.other()


def positives() -> None:
    """Every statement here should be flagged as a discarded Result/Option."""
    Ok(1)
    Err("bad")
    Some(1)
    Nothing()
    make()
    r = make()
    r.map(str)


def negatives() -> None:
    """None of these statements should be flagged."""
    x = Ok(1)
    helper()
    y = make()
    z = y.map(str)
    Ok(1).inspect(print)
    Ok(1).inspect_err(print)
    assert x is not None
    assert z is not None
