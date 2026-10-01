from typing import cast

import pytest

from radixscope.core import FixedWidthInteger


def test_bitwise_operations_preserve_format_and_operands() -> None:
    left = FixedWidthInteger(0b1010, 4)
    right = FixedWidthInteger(0b1100, 4)
    assert (left & right) == FixedWidthInteger(0b1000, 4)
    assert (left | right) == FixedWidthInteger(0b1110, 4)
    assert (left ^ right) == FixedWidthInteger(0b0110, 4)
    assert (~left) == FixedWidthInteger(0b0101, 4)
    assert left.value == 0b1010
    assert right.value == 0b1100


def test_signed_bitwise_result_uses_twos_complement() -> None:
    negative = FixedWidthInteger(-1, 8, True)
    mask = FixedWidthInteger(15, 8, True)
    assert (negative & mask).value == 15
    assert (negative ^ mask).value == -16
    assert (~negative).value == 0
    assert (~FixedWidthInteger(15, 5, True)).value == -16


def test_signed_and_logical_right_shifts_differ() -> None:
    value = FixedWidthInteger(-128, 8, True)
    assert (value >> 1).value == -64
    assert value.logical_right_shift(1).value == 64
    assert (FixedWidthInteger(128, 8) >> 1).value == 64
    assert (value << 1).value == 0


@pytest.mark.parametrize("count", [8, 9, 10**100])
def test_large_shift_counts_do_not_create_unbounded_integers(count: int) -> None:
    negative = FixedWidthInteger(-5, 8, True)
    positive = FixedWidthInteger(255, 8)
    assert (negative >> count).value == -1
    assert negative.logical_right_shift(count).value == 0
    assert (negative << count).value == 0
    assert (positive >> count).value == 0


@pytest.mark.parametrize("count", [-1, True, 1.5, "1"])
def test_invalid_shift_counts_are_rejected(count: object) -> None:
    value = FixedWidthInteger(1, 8)
    for shift in (value.__lshift__, value.__rshift__, value.logical_right_shift):
        with pytest.raises((TypeError, ValueError)):
            shift(count)


def test_mismatched_bitwise_operands_are_rejected() -> None:
    value = FixedWidthInteger(1, 8)
    for other in (FixedWidthInteger(1, 16), FixedWidthInteger(1, 8, True)):
        with pytest.raises(ValueError):
            _ = value & other
    with pytest.raises(TypeError):
        _ = value | cast(FixedWidthInteger, 1)


def test_bitwise_identities_across_widths() -> None:
    for width in (1, 5, 8, 16):
        zero = FixedWidthInteger(0, width)
        ones = FixedWidthInteger((1 << width) - 1, width)
        assert (~zero) == ones
        assert (~ones) == zero
        assert (ones ^ ones) == zero
        assert (ones << 0) == ones
        assert (ones >> 0) == ones
