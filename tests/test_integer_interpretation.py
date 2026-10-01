import pytest

from radixscope.core import (
    FixedWidthInteger,
    IntegerRangeError,
    InvalidNumberError,
    interpret_bit_pattern,
    parse_bit_pattern,
)


@pytest.mark.parametrize(
    ("pattern", "width", "signed"), [(255, 8, -1), (128, 8, -128), (127, 8, 127), (1, 1, -1)]
)
def test_same_pattern_has_two_interpretations(pattern: int, width: int, signed: int) -> None:
    report = interpret_bit_pattern(pattern, width)
    assert report.unsigned_value == pattern
    assert report.signed_value == signed
    assert report.sign_bit == int(signed < 0)
    assert len(report.binary) == width
    assert int(report.hexadecimal, 16) == pattern


def test_declared_width_changes_sign_interpretation() -> None:
    assert FixedWidthInteger.from_bits("11111111", signed=True).value == -1
    assert FixedWidthInteger.from_bits("11111111", 16, signed=True).value == 255
    assert parse_bit_pattern("FF", 16, 8, signed=True).value == -1
    assert parse_bit_pattern("FF", 16, 16, signed=True).value == 255


def test_non_nibble_width_is_padded() -> None:
    report = interpret_bit_pattern(31, 5)
    assert report.binary == "11111"
    assert report.hexadecimal == "1F"
    assert report.signed_value == -1


def test_excess_bits_are_not_discarded() -> None:
    with pytest.raises(IntegerRangeError):
        FixedWidthInteger.from_bits("00000", 4)
    with pytest.raises(IntegerRangeError):
        parse_bit_pattern("100", 16, 8)
    with pytest.raises(IntegerRangeError):
        parse_bit_pattern("-1", 10, 8)


@pytest.mark.parametrize("bits", ["", "0b1", "1 0", "2"])
def test_bit_text_requires_raw_binary(bits: str) -> None:
    with pytest.raises(InvalidNumberError):
        FixedWidthInteger.from_bits(bits)
