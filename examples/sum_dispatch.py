"""
Sum + dispatch example.

Shows exhaustive tagged-union dispatch with Sum, and open-ended dispatch
with the dispatch() function.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typani import Sum, dispatch

# ---------------------------------------------------------------------------
# Variant types
# ---------------------------------------------------------------------------


@dataclass
class Circle:
    radius: float


@dataclass
class Rectangle:
    width: float
    height: float


@dataclass
class Triangle:
    base: float
    height: float


Shape = Sum[Circle, Triangle, Rectangle]


# ---------------------------------------------------------------------------
# Exhaustive dispatch with Sum.match
# ---------------------------------------------------------------------------


def area(shape: object) -> float:
    return Shape.match(
        shape,
        {
            Circle: lambda c: math.pi * c.radius**2,
            Triangle: lambda t: 0.5 * t.base * t.height,
            Rectangle: lambda r: r.width * r.height,
        },
    )


def describe(shape: object) -> str:
    return Shape.match(
        shape,
        {
            Circle: lambda c: f"circle with radius {c.radius}",
            Triangle: lambda t: f"triangle (base {t.base}, height {t.height})",
            Rectangle: lambda r: f"{r.width}x{r.height} rectangle",
        },
    )


# ---------------------------------------------------------------------------
# Open-ended dispatch without Sum
# ---------------------------------------------------------------------------


def render(value: object) -> str:
    """
    Open-ended dispatch that handles a wider range of types.
    No upfront closed set; 'default' handles anything unexpected.
    """
    return dispatch(
        value,
        {
            Circle: lambda c: f"<circle r={c.radius:.2f}>",
            Rectangle: lambda r: f"<rect {r.width:.2f}x{r.height:.2f}>",
            Triangle: lambda t: f"<tri b={t.base:.2f} h={t.height:.2f}>",
            int: lambda n: f"<int {n}>",
            str: lambda s: f"<str {s!r}>",
        },
        default="<unknown>",
    )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def main() -> None:
    shapes: list[object] = [
        Circle(radius=3.0),
        Rectangle(width=4.0, height=5.0),
        Triangle(base=6.0, height=2.0),
    ]

    print("=== areas ===")
    for s in shapes:
        print(f"  {describe(s)}: area = {area(s):.4f}")

    print()
    print("=== render (open-ended) ===")
    mixed: list[object] = shapes + [42, "hello", 3.14]
    for v in mixed:
        print(f"  {render(v)}")

    print()
    print("=== exhaustiveness check ===")
    try:
        # Remove one handler to trigger the exhaustiveness error
        Shape.match(
            Circle(radius=1.0),
            {
                Circle: lambda c: "circle",
                # Rectangle and Triangle intentionally missing
            },
        )
    except TypeError as exc:
        print(f"  Caught: {exc}")


if __name__ == "__main__":
    main()
