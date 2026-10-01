import pytest

from radixscope.core import (
    ArithmeticOperation,
    FixedWidthInteger,
    IntegerRangeError,
    analyze_arithmetic,
    analyze_range,
)


@pytest.mark.parametrize(
    ("value", "signed", "overflowed", "wrapped"),
    [
        (255, False, False, 255),
        (256, False, True, 0),
        (-1, False, True, 255),
        (127, True, False, 127),
        (-128, True, False, -128),
        (128, True, True, -128),
        (-129, True, True, 127),
        (513, False, True, 1),
    ],
)
def test_range_analysis_preserves_exact_result(
    value: int, signed: bool, overflowed: bool, wrapped: int
) -> None:
    result = analyze_range(value, 8, signed)
    assert result.exact_value == value
    assert result.overflowed == overflowed
    assert result.wrapped.value == wrapped
    if overflowed:
        with pytest.raises(IntegerRangeError):
            _ = result.checked
    else:
        assert result.checked.value == value


@pytest.mark.parametrize(
    ("left", "right", "signed", "operation", "exact", "wrapped"),
    [
        (127, 1, True, ArithmeticOperation.ADD, 128, -128),
        (-128, 1, True, ArithmeticOperation.SUBTRACT, -129, 127),
        (255, 1, False, ArithmeticOperation.ADD, 256, 0),
        (0, 1, False, ArithmeticOperation.SUBTRACT, -1, 255),
        (16, 16, False, ArithmeticOperation.MULTIPLY, 256, 0),
        (-128, -1, True, ArithmeticOperation.MULTIPLY, 128, -128),
    ],
)
def test_arithmetic_overflow(
    left: int,
    right: int,
    signed: bool,
    operation: ArithmeticOperation,
    exact: int,
    wrapped: int,
) -> None:
    result = analyze_arithmetic(
        FixedWidthInteger(left, 8, signed), FixedWidthInteger(right, 8, signed), operation
    )
    assert result.overflowed
    assert result.exact_value == exact
    assert result.wrapped.value == wrapped


def test_in_range_arithmetic_is_unchanged() -> None:
    result = analyze_arithmetic(
        FixedWidthInteger(-5, 8, True), FixedWidthInteger(7, 8, True), ArithmeticOperation.ADD
    )
    assert not result.overflowed
    assert result.checked == result.wrapped == FixedWidthInteger(2, 8, True)


def test_mismatched_operand_formats_are_rejected() -> None:
    with pytest.raises(ValueError, match="same width"):
        analyze_arithmetic(
            FixedWidthInteger(1, 8), FixedWidthInteger(1, 16), ArithmeticOperation.ADD
        )
    with pytest.raises(ValueError, match="signedness"):
        analyze_arithmetic(
            FixedWidthInteger(1, 8), FixedWidthInteger(1, 8, True), ArithmeticOperation.ADD
        )


def test_nonstandard_width_overflow() -> None:
    assert analyze_range(32, 5).wrapped.value == 0
    assert analyze_range(16, 5, True).wrapped.value == -16
    assert analyze_range(-17, 5, True).wrapped.value == 15
