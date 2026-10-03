import math
import struct

import pytest

from radixscope.core import (
    ExactValue,
    FloatClass,
    IEEEFormat,
    decode_ieee754,
    decode_ieee754_bytes,
    encode_ieee754,
    encode_ieee754_special,
)


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_every_finite_exponent_matches_struct_and_round_trips(width: IEEEFormat) -> None:
    mask = (1 << width.fraction_width) - 1
    code = ">f" if width is IEEEFormat.BINARY32 else ">d"
    for exponent in range((1 << width.exponent_width) - 1):
        for fraction in (0, 1, mask // 2, mask):
            for sign in (0, 1):
                pattern = (
                    (sign << (width.value - 1)) | (exponent << width.fraction_width) | fraction
                )
                raw = pattern.to_bytes(width.value // 8, "big")
                expected: float = struct.unpack(code, raw)[0]
                decoded = decode_ieee754(pattern, width)
                assert decoded.exact == ExactValue(*expected.as_integer_ratio())
                assert decoded.exact is not None
                negative_zero = decoded.classification is FloatClass.ZERO and sign == 1
                assert encode_ieee754(decoded.exact, width, negative_zero=negative_zero) == decoded


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_midpoints_at_every_normal_exponent_choose_even_neighbor(width: IEEEFormat) -> None:
    for exponent in range(1, (1 << width.exponent_width) - 1):
        for fraction in (0, 1, (1 << width.fraction_width) - 2):
            pattern = (exponent << width.fraction_width) | fraction
            lower = decode_ieee754(pattern, width).exact
            upper = decode_ieee754(pattern + 1, width).exact
            assert lower is not None and upper is not None
            midpoint = (lower + upper) / ExactValue(2)
            expected = pattern + pattern % 2
            assert encode_ieee754(midpoint, width).pattern == expected
            epsilon = (upper - lower) / ExactValue(1 << 100)
            assert encode_ieee754(midpoint - epsilon, width).pattern == pattern
            assert encode_ieee754(midpoint + epsilon, width).pattern == pattern + 1


@pytest.mark.parametrize("width", [IEEEFormat.BINARY32, IEEEFormat.BINARY64])
def test_nan_payload_and_signaling_status_survive_each_byte_order(width: IEEEFormat) -> None:
    quiet_bit = 1 << (width.fraction_width - 1)
    for payload in (1, 2, 7, quiet_bit // 2, quiet_bit - 1):
        for quiet in (False, True):
            for sign in (0, 1):
                value = encode_ieee754_special(
                    "nan", width, sign_bit=sign, payload=payload, quiet=quiet
                )
                for order in ("big", "little"):
                    restored = decode_ieee754_bytes(value.to_bytes(order), width, order)
                    assert restored == value
                    assert restored.nan_payload == payload
                    assert restored.is_quiet_nan is quiet
                    assert restored.sign_bit == sign


@pytest.mark.parametrize(
    "width,hexadecimal,classification,negative",
    [
        (32, "00000000", FloatClass.ZERO, False),
        (32, "80000000", FloatClass.ZERO, True),
        (32, "00000001", FloatClass.SUBNORMAL, False),
        (32, "007FFFFF", FloatClass.SUBNORMAL, False),
        (32, "00800000", FloatClass.NORMAL, False),
        (32, "7F7FFFFF", FloatClass.NORMAL, False),
        (32, "7F800000", FloatClass.INFINITY, False),
        (32, "FF800000", FloatClass.INFINITY, True),
        (32, "7FC00000", FloatClass.NAN, False),
        (64, "0000000000000000", FloatClass.ZERO, False),
        (64, "8000000000000000", FloatClass.ZERO, True),
        (64, "0000000000000001", FloatClass.SUBNORMAL, False),
        (64, "000FFFFFFFFFFFFF", FloatClass.SUBNORMAL, False),
        (64, "0010000000000000", FloatClass.NORMAL, False),
        (64, "7FEFFFFFFFFFFFFF", FloatClass.NORMAL, False),
        (64, "7FF0000000000000", FloatClass.INFINITY, False),
        (64, "FFF0000000000000", FloatClass.INFINITY, True),
        (64, "7FF8000000000000", FloatClass.NAN, False),
    ],
)
def test_published_boundary_vectors(
    width: int, hexadecimal: str, classification: FloatClass, negative: bool
) -> None:
    decoded = decode_ieee754_bytes(bytes.fromhex(hexadecimal), width)
    assert decoded.hexadecimal == hexadecimal
    assert decoded.classification is classification
    assert bool(decoded.sign_bit) is negative
    if classification is FloatClass.NAN:
        assert math.isnan(decoded.to_float())
    else:
        assert (math.copysign(1, decoded.to_float()) < 0) is negative
