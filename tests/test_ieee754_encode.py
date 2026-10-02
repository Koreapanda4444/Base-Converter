import math
import random
import struct
from fractions import Fraction
from typing import cast

import pytest

from radixscope.core import (
    ExactValue,
    FloatClass,
    IEEEFormat,
    decode_ieee754,
    encode_ieee754,
    encode_ieee754_special,
)


@pytest.mark.parametrize("width,code", [(32, ">f"), (64, ">d")])
def test_known_values_match_struct(width: int, code: str) -> None:
    for value in (0.0, -0.0, 0.1, -0.1, 1.5, -10.0, 2**24 + 1, math.inf, -math.inf):
        assert encode_ieee754(value, width).to_bytes() == struct.pack(code, value)
    assert encode_ieee754(ExactValue(1, 10), width).to_bytes() == struct.pack(code, 0.1)


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_rational_rounding_ties_choose_even_significand(width: IEEEFormat) -> None:
    one = width.bias << width.fraction_width
    step = Fraction(1, 1 << width.fraction_width)
    for lower in (0, 1, 2, 3):
        midpoint = Fraction(1) + (Fraction(lower) + Fraction(1, 2)) * step
        expected = one + lower + lower % 2
        epsilon = step / (1 << 100)
        assert encode_ieee754(ExactValue.from_fraction(midpoint), width).pattern == expected
        below = encode_ieee754(ExactValue.from_fraction(midpoint - epsilon), width)
        above = encode_ieee754(ExactValue.from_fraction(midpoint + epsilon), width)
        assert below.pattern == one + lower
        assert above.pattern == one + lower + 1
        negative = encode_ieee754(ExactValue.from_fraction(-midpoint), width)
        assert negative.pattern == expected | (1 << (width.value - 1))


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_subnormal_and_normal_transition_rounding(width: IEEEFormat) -> None:
    unit = Fraction(1, 1 << (width.bias + width.fraction_width - 1))
    for numerator, expected in ((1, 0), (3, 2), (5, 2)):
        midpoint = ExactValue.from_fraction(unit * Fraction(numerator, 2))
        assert encode_ieee754(midpoint, width).pattern == expected
    half_minimum = ExactValue.from_fraction(-unit / 2)
    negative_zero = encode_ieee754(half_minimum, width)
    assert negative_zero.classification is FloatClass.ZERO
    assert negative_zero.sign_bit == 1
    normal_pattern = 1 << width.fraction_width
    midpoint = ExactValue.from_fraction(unit * Fraction(2 * normal_pattern - 1, 2))
    assert encode_ieee754(midpoint, width).pattern == normal_pattern
    below = ExactValue.from_fraction(midpoint.fraction - unit / 100)
    assert encode_ieee754(below, width).pattern == normal_pattern - 1


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_significand_carry_and_overflow_threshold(width: IEEEFormat) -> None:
    below_two = ExactValue((1 << (width.fraction_width + 2)) - 1, 1 << (width.fraction_width + 1))
    assert encode_ieee754(below_two, width).exact == ExactValue(2)
    infinity_pattern = ((1 << width.exponent_width) - 1) << width.fraction_width
    maximum = decode_ieee754(infinity_pattern - 1, width).exact
    assert maximum is not None
    half_step = ExactValue(1 << (width.bias - width.fraction_width - 1))
    threshold = maximum + half_step
    assert encode_ieee754(maximum, width).pattern == infinity_pattern - 1
    assert encode_ieee754(threshold - ExactValue(1), width).pattern == infinity_pattern - 1
    assert encode_ieee754(threshold, width).classification is FloatClass.INFINITY
    assert encode_ieee754(-threshold, width).sign_bit == 1
    assert encode_ieee754(1 << 10000, width).classification is FloatClass.INFINITY
    assert encode_ieee754(ExactValue(1, 1 << 10000), width).pattern == 0


@pytest.mark.parametrize("width", [32, 64])
def test_seeded_finite_patterns_round_trip_through_exact_values(width: int) -> None:
    generator = random.Random(32 + width)
    patterns = [0, 1, 1 << (width - 1), (1 << (width - 1)) | 1]
    patterns.extend(generator.getrandbits(width) for _ in range(1000))
    for pattern in patterns:
        decoded = decode_ieee754(pattern, width)
        if decoded.exact is not None:
            negative_zero = decoded.classification is FloatClass.ZERO and decoded.sign_bit == 1
            encoded = encode_ieee754(decoded.exact, width, negative_zero=negative_zero)
            assert encoded.pattern == pattern


@pytest.mark.parametrize("width,code", [(32, ">f"), (64, ">d")])
def test_seeded_rational_values_match_independent_reference(width: int, code: str) -> None:
    generator = random.Random(754 + width)
    for _ in range(1000):
        rational = Fraction(
            generator.randrange(-(1 << 60), 1 << 60), generator.randrange(1, 1 << 60)
        )
        expected = struct.pack(code, float(rational))
        if width == 32:
            rounded = decode_ieee754(int.from_bytes(expected, "big"), width)
            assert rounded.exact is not None
            difference = abs(rational - rounded.exact.fraction)
            for neighbor in (rounded.pattern - 1, rounded.pattern + 1):
                adjacent = decode_ieee754(neighbor, width).exact
                assert adjacent is not None
                assert difference <= abs(rational - adjacent.fraction)
        assert encode_ieee754(ExactValue.from_fraction(rational), width).to_bytes() == expected


@pytest.mark.parametrize("width,code", [(32, ">f"), (64, ">d")])
def test_host_float_encoding_across_seeded_binary64_exponents(width: int, code: str) -> None:
    generator = random.Random(3200 + width)
    for _ in range(1000):
        data = generator.getrandbits(64).to_bytes(8, "big")
        value = struct.unpack(">d", data)[0]
        if math.isnan(value):
            continue
        try:
            expected = struct.pack(code, value)
        except OverflowError:
            expected = struct.pack(code, math.copysign(math.inf, value))
        assert encode_ieee754(value, width).to_bytes() == expected


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_explicit_special_values_and_nan_payloads(width: IEEEFormat) -> None:
    for sign in (0, 1):
        zero = encode_ieee754_special("zero", width, sign_bit=sign)
        assert zero.classification is FloatClass.ZERO
        assert zero.sign_bit == sign
        assert encode_ieee754(0, width, negative_zero=bool(sign)) == zero
        infinity = encode_ieee754_special("infinity", width, sign_bit=sign)
        assert infinity.classification is FloatClass.INFINITY
        assert infinity.sign_bit == sign
        for quiet in (False, True):
            for payload in (1, 123, (1 << (width.fraction_width - 1)) - 1):
                nan = encode_ieee754_special(
                    "nan", width, sign_bit=sign, quiet=quiet, payload=payload
                )
                assert nan.sign_bit == sign
                assert nan.is_quiet_nan is quiet
                assert nan.nan_payload == payload
                assert nan.classification is FloatClass.NAN
        canonical = encode_ieee754_special("nan", width, sign_bit=sign)
        assert canonical.is_quiet_nan
        assert canonical.nan_payload == 0
    assert encode_ieee754(float("nan"), width).is_quiet_nan


@pytest.mark.parametrize("value", [True, "1.0", None, Fraction(1, 3)])
def test_invalid_numeric_input_is_rejected(value: object) -> None:
    with pytest.raises(TypeError):
        encode_ieee754(cast(ExactValue, value))


def test_invalid_special_value_metadata_is_rejected() -> None:
    for kind in ("normal", "subnormal", "unknown", 1):
        with pytest.raises((TypeError, ValueError)):
            encode_ieee754_special(kind)
    for sign in (-1, 2, True, "1"):
        with pytest.raises((TypeError, ValueError)):
            encode_ieee754_special("zero", sign_bit=sign)
    for payload in (-1, 1 << 22, True, "1"):
        with pytest.raises((TypeError, ValueError)):
            encode_ieee754_special("nan", 32, payload=payload)
    with pytest.raises(ValueError):
        encode_ieee754_special("nan", quiet=False)
    with pytest.raises(ValueError):
        encode_ieee754_special("infinity", payload=1)
    with pytest.raises(TypeError):
        encode_ieee754_special("nan", quiet=cast(bool, 1))
    with pytest.raises(TypeError):
        encode_ieee754(0, negative_zero=cast(bool, 1))
    for value in (1, math.inf):
        with pytest.raises(ValueError):
            encode_ieee754(value, negative_zero=True)
