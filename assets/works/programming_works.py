"""Geometric calculator functions (pure Python).

The browser page and shared shell live in works/pages/programming_works.py.
"""

import math

NO_INPUT_MESSAGE = "Enter a measurement to begin."


def to_number(raw):
    """Like JavaScript's Number(): '' is 0, junk is NaN."""
    raw = (raw or "").strip()
    if raw == "":
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return math.nan


def format_area(value):
    """Up to two decimals with thousands separators, e.g. 1,234.5"""
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def circle_area(radius):
    return math.pi * radius * radius


def triangle_area(base, height):
    return 0.5 * base * height


def area_message(shape, radius=0.0, base=0.0, height=0.0):
    """The sentence shown under the form for a given shape and measurements."""
    values = [radius] if shape == "circle" else [base, height]
    if any(not math.isfinite(value) or value <= 0 for value in values):
        return "Please enter measurements greater than zero."
    if shape == "circle":
        return f"Circle area: {format_area(circle_area(radius))} square units."
    return f"Triangle area: {format_area(triangle_area(base, height))} square units."
