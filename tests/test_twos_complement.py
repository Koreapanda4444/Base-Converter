import pytest

from radixscope.core import (
    FixedWidthInteger,
    IntegerRangeError,
    decode_twos_complement,
    encode_twos_complement,
    format_twos_complement,
    parse_twos_complement,
)


@pytest.mark.parametrize(
    ("value", "width", "pattern"),
    [
        (0, 8, 0),
        (1, 8, 1),
        (127, 8, 127),
        (-1, 8, 255),
        (-128, 8, 128),
        (-32768, 16, 32768),
    ],
)
def test_twos_complement_round_trip(value: int, width: int, pattern: int) -> None:
    assert encode_twos_complement(value, width) == pattern
    assert decode_twos_complement(pattern, width) == value


def test_twos_complement_bit_format() -> None:
    assert format_twos_complement(-5, 8) == "11111011"
    assert parse_twos_complement("11111011") == FixedWidthInteger(-5, 8, signed=True)


def test_fixed_width_bit_pattern() -> None:
    signed = FixedWidthInteger(-1, 8, signed=True)

    assert signed.bit_pattern == 255
    assert signed.bits == "11111111"
    assert signed.reinterpret(signed=False) == FixedWidthInteger(255, 8)
    assert signed.reinterpret(signed=False).reinterpret(signed=True) == signed


@pytest.mark.parametrize(
    ("value", "width"),
    [
        (-129, 8),
        (128, 8),
        (-2, 1),
        (1, 1),
    ],
)
def test_twos_complement_value_out_of_range(value: int, width: int) -> None:
    with pytest.raises(IntegerRangeError):
        encode_twos_complement(value, width)


@pytest.mark.parametrize("pattern", [-1, 256])
def test_twos_complement_pattern_out_of_range(pattern: int) -> None:
    with pytest.raises(IntegerRangeError):
        decode_twos_complement(pattern, 8)


@pytest.mark.parametrize("bits", ["", "102", " 01", "0b01"])
def test_invalid_twos_complement_text(bits: str) -> None:
    with pytest.raises(ValueError):
        parse_twos_complement(bits)
