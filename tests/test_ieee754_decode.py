import math
import random
import struct

import pytest

from radixscope.core import (
    ExactValue,
    FloatClass,
    IEEEFormat,
    IntegerRangeError,
    decode_ieee754,
    decode_ieee754_bytes,
)


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_field_layout_and_known_finite_values(width: IEEEFormat) -> None:
    fraction_width = width.fraction_width
    one = width.bias << fraction_width
    decoded = decode_ieee754(one, width)
    assert decoded.classification is FloatClass.NORMAL
    assert decoded.exact == ExactValue(1)
    assert decoded.significand == ExactValue(1)
    assert decoded.exponent == 0
    assert decoded.exponent_bits == width.bias
    assert decoded.fraction_bits == 0
    negative = decode_ieee754(one | (1 << (width.value - 1)), width)
    assert negative.exact == ExactValue(-1)
    assert negative.sign_bit == 1
    assert decode_ieee754(one | (1 << (fraction_width - 1)), width).exact == ExactValue(3, 2)


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_normal_and_subnormal_boundaries_are_exact(width: IEEEFormat) -> None:
    unit_denominator = 1 << (width.bias + width.fraction_width - 1)
    minimum = decode_ieee754(1, width)
    assert minimum.classification is FloatClass.SUBNORMAL
    assert minimum.exact == ExactValue(1, unit_denominator)
    largest = decode_ieee754((1 << width.fraction_width) - 1, width)
    smallest_normal = decode_ieee754(1 << width.fraction_width, width)
    assert largest.classification is FloatClass.SUBNORMAL
    assert smallest_normal.classification is FloatClass.NORMAL
    assert largest.exact == ExactValue((1 << width.fraction_width) - 1, unit_denominator)
    assert smallest_normal.exact == ExactValue(1 << width.fraction_width, unit_denominator)


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_zeros_infinities_and_nan_metadata_preserve_raw_bits(width: IEEEFormat) -> None:
    special = ((1 << width.exponent_width) - 1) << width.fraction_width
    quiet = 1 << (width.fraction_width - 1)
    for sign in (0, 1):
        sign_bits = sign << (width.value - 1)
        zero = decode_ieee754(sign_bits, width)
        assert zero.classification is FloatClass.ZERO
        assert zero.exact == ExactValue(0)
        assert math.copysign(1, zero.to_float()) == (-1 if sign else 1)
        infinity = decode_ieee754(sign_bits | special, width)
        assert infinity.classification is FloatClass.INFINITY
        assert infinity.exact is None
        assert infinity.significand is None
        assert infinity.exponent is None
        assert math.isinf(infinity.to_float())
        for fraction, is_quiet in ((7, False), (quiet, True), (quiet | 7, True)):
            nan = decode_ieee754(sign_bits | special | fraction, width)
            assert nan.classification is FloatClass.NAN
            assert nan.exact is None
            assert nan.is_quiet_nan is is_quiet
            assert nan.nan_payload == (fraction & (quiet - 1))
            assert nan.pattern == sign_bits | special | fraction
            assert math.isnan(nan.to_float())
            assert decode_ieee754_bytes(nan.to_bytes(), width) == nan
        assert infinity.nan_payload is None
        assert not infinity.is_quiet_nan


@pytest.mark.parametrize("width,code", [(32, ">f"), (64, ">d")])
def test_decoding_matches_struct_for_seeded_raw_patterns(width: int, code: str) -> None:
    generator = random.Random(31 + width)
    for _ in range(1000):
        pattern = generator.getrandbits(width)
        data = pattern.to_bytes(width // 8, "big")
        reference = struct.unpack(code, data)[0]
        decoded = decode_ieee754(pattern, width)
        assert decoded.to_bytes() == data
        assert decode_ieee754_bytes(data[::-1], width, "little") == decoded
        assert int(decoded.bits, 2) == int(decoded.hexadecimal, 16) == pattern
        if math.isfinite(reference):
            assert decoded.exact == ExactValue(*reference.as_integer_ratio())
        elif math.isnan(reference):
            assert decoded.classification is FloatClass.NAN
        else:
            assert decoded.classification is FloatClass.INFINITY


@pytest.mark.parametrize("width", [16, 80, 128, 0, -32, True, "32", 32.0])
def test_unsupported_formats_are_rejected(width: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        decode_ieee754(0, width)


def test_invalid_patterns_and_byte_lengths_are_rejected() -> None:
    for pattern in (-1, 1 << 32):
        with pytest.raises(IntegerRangeError):
            decode_ieee754(pattern, 32)
    for invalid_pattern in (True, 1.5, "0"):
        with pytest.raises(TypeError):
            decode_ieee754(invalid_pattern, 32)
    with pytest.raises(IntegerRangeError):
        decode_ieee754_bytes(b"\x00" * 8, 32)
