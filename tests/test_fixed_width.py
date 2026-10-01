from typing import cast

import pytest

from radixscope.core import (
    ExactValue,
    FixedWidthInteger,
    IntegerRangeError,
    InvalidWidthError,
    NonIntegerValueError,
    integer_bounds,
)


@pytest.mark.parametrize(
    ("width", "signed", "expected"),
    [
        (1, False, (0, 1)),
        (1, True, (-1, 0)),
        (8, False, (0, 255)),
        (8, True, (-128, 127)),
        (64, True, (-(1 << 63), (1 << 63) - 1)),
    ],
)
def test_integer_bounds(width: int, signed: bool, expected: tuple[int, int]) -> None:
    assert integer_bounds(width, signed) == expected


def test_fixed_width_integer_properties() -> None:
    value = FixedWidthInteger(-128, 8, signed=True)

    assert value.minimum == -128
    assert value.maximum == 127
    assert value.modulus == 256
    assert value.is_negative


@pytest.mark.parametrize("width", [0, -1, True, 8.0])
def test_invalid_width(width: object) -> None:
    with pytest.raises(InvalidWidthError):
        FixedWidthInteger(0, cast(int, width))


@pytest.mark.parametrize(
    ("value", "width", "signed"),
    [
        (-1, 8, False),
        (256, 8, False),
        (-129, 8, True),
        (128, 8, True),
    ],
)
def test_out_of_range_integer(value: int, width: int, signed: bool) -> None:
    with pytest.raises(IntegerRangeError):
        FixedWidthInteger(value, width, signed)


@pytest.mark.parametrize("value", [True, 1.5, "1"])
def test_fixed_width_value_must_be_integer(value: object) -> None:
    with pytest.raises(TypeError):
        FixedWidthInteger(cast(int, value), 8)


def test_fixed_width_exact_value_bridge() -> None:
    source = ExactValue(-126, 2)
    value = FixedWidthInteger.from_exact(source, 8, signed=True)
    assert value.value == -63
    assert value.exact == source
    assert value.resize(16).value == -63
    assert value.width == 8
    assert value.resize(16).bits == "1111111111000001"


@pytest.mark.parametrize(
    ("text", "base", "width", "signed", "expected"),
    [
        ("FF", 16, 8, False, 255),
        ("-10000000", 2, 8, True, -128),
        ("1.(9)", 10, 8, False, 2),
        ("1F", 16, 5, False, 31),
    ],
)
def test_fixed_width_input(
    text: str, base: int, width: int, signed: bool, expected: int
) -> None:
    assert FixedWidthInteger.from_text(text, base, width, signed).value == expected


def test_fraction_cannot_be_silently_truncated() -> None:
    with pytest.raises(NonIntegerValueError):
        FixedWidthInteger.from_text("1/2", 10, 8)


def test_resize_checks_target_range() -> None:
    with pytest.raises(IntegerRangeError):
        FixedWidthInteger(255, 16).resize(7)
    with pytest.raises(IntegerRangeError):
        FixedWidthInteger(-129, 16, signed=True).resize(8)
    assert FixedWidthInteger(-128, 16, signed=True).resize(8).value == -128
