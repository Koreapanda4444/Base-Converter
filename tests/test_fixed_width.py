import pytest

from radixscope.core import (
    FixedWidthInteger,
    IntegerRangeError,
    InvalidWidthError,
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
        FixedWidthInteger(0, width)


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
        FixedWidthInteger(value, 8)
