import pytest

from typani.sum import Sum

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class Circle:
    def __init__(self, radius: float) -> None:
        self.radius = radius


class Square:
    def __init__(self, side: float) -> None:
        self.side = side


class Triangle:
    def __init__(self, base: float, height: float) -> None:
        self.base = base
        self.height = height


Shape = Sum[Circle, Square, Triangle]
Number = Sum[int, float]


# ---------------------------------------------------------------------------
# Subscript creates a named subclass
# ---------------------------------------------------------------------------


# frob:tests src/typani/sum.py kind="integration"
def test_sum_name_reflects_variants() -> None:
    assert Shape.__name__ == "Sum[Circle, Square, Triangle]"


def test_single_variant() -> None:
    S = Sum[int]
    assert S._variants == (int,)


def test_variants_tuple() -> None:
    assert Shape._variants == (Circle, Square, Triangle)


# ---------------------------------------------------------------------------
# check()
# ---------------------------------------------------------------------------


def test_check_matching_variant() -> None:
    assert Shape.check(Circle(1.0))
    assert Shape.check(Square(2.0))
    assert Shape.check(Triangle(3.0, 4.0))


def test_check_non_matching() -> None:
    assert not Shape.check("hello")
    assert not Shape.check(42)


def test_check_empty_sum() -> None:
    assert not Sum.check("anything")


def test_check_subclass_of_variant() -> None:
    class SubCircle(Circle):
        pass

    assert Shape.check(SubCircle(1.0))


# ---------------------------------------------------------------------------
# match() -- exhaustive
# ---------------------------------------------------------------------------


# Sum.match delegates to dispatch() internally, so this exercises the
# sum.py <-> dispatch.py boundary end to end.
# frob:tests src/typani/dispatch.py kind="integration"
def test_match_dispatches_correctly() -> None:
    area = Shape.match(
        Circle(1.0),
        {
            Circle: lambda c: 3.14 * c.radius**2,
            Square: lambda s: s.side**2,
            Triangle: lambda t: 0.5 * t.base * t.height,
        },
    )
    assert abs(area - 3.14) < 0.01


def test_match_raises_on_missing_variant() -> None:
    with pytest.raises(TypeError, match="Non-exhaustive"):
        Shape.match(
            Circle(1.0),
            {
                Circle: lambda c: c.radius,
                # Square and Triangle missing
            },
        )


def test_match_error_names_missing_variants() -> None:
    with pytest.raises(TypeError, match="Square"):
        Shape.match(Circle(1.0), {Circle: lambda c: 0, Triangle: lambda t: 0})


def test_match_with_default_allows_partial() -> None:
    result = Shape.match(
        Circle(1.0),
        {Circle: lambda c: "circle"},
        default="other",
    )
    assert result == "circle"


def test_match_default_used_for_unhandled() -> None:
    result = Shape.match(
        Square(2.0),
        {Circle: lambda c: "circle"},
        default="not a circle",
    )
    assert result == "not a circle"


def test_match_first_matching_case_wins() -> None:
    result = Shape.match(
        Circle(5.0),
        {
            Circle: lambda c: "first",
            object: lambda _: "second",
            Square: lambda s: "third",
            Triangle: lambda t: "fourth",
        },
    )
    assert result == "first"


# ---------------------------------------------------------------------------
# Interoperability with built-in types
# ---------------------------------------------------------------------------


def test_match_builtin_types() -> None:
    result = Number.match(
        42,
        {int: lambda n: n * 2, float: lambda f: f + 0.5},
    )
    assert result == 84


def test_match_str_and_int() -> None:
    StringOrInt = Sum[str, int]
    assert StringOrInt.match("hi", {str: str.upper, int: str}) == "HI"
    assert StringOrInt.match(7, {str: str.upper, int: str}) == "7"


# ---------------------------------------------------------------------------
# Sum with no variants (base Sum class)
# ---------------------------------------------------------------------------


def test_base_sum_match_acts_like_dispatch() -> None:
    result = Sum.match("hello", {str: str.upper, int: str}, default="?")
    assert result == "HELLO"


def test_base_sum_no_exhaustiveness_check() -> None:
    # Base Sum has no declared variants, so no exhaustiveness check fires
    result = Sum.match(42, {int: lambda n: n + 1}, default=0)
    assert result == 43
