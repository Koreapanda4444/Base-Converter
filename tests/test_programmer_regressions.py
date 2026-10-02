import pytest

from radixscope.core import (
    ArithmeticOperation,
    ExactValue,
    FixedWidthInteger,
    IntegerRangeError,
    analyze_arithmetic,
    decode_ascii,
    decode_bytes,
    decode_twos_complement,
    encode_ascii,
    encode_bytes,
    encode_twos_complement,
    interpret_bit_pattern,
    represent_bytes,
)


@pytest.mark.parametrize("width", range(1, 7))
def test_every_small_pattern_preserves_both_interpretations(width: int) -> None:
    modulus = 1 << width
    for pattern in range(modulus):
        signed_value = pattern if pattern < modulus // 2 else pattern - modulus
        unsigned = FixedWidthInteger(pattern, width)
        signed = unsigned.reinterpret(True)
        report = interpret_bit_pattern(pattern, width)
        assert signed.value == signed_value
        assert signed.exact == ExactValue(signed_value)
        assert signed.reinterpret(False) == unsigned
        assert encode_twos_complement(signed_value, width) == pattern
        assert decode_twos_complement(pattern, width) == signed_value
        assert int(report.binary, 2) == int(report.hexadecimal, 16) == pattern
        assert report.signed_value == signed_value
        for order in ("big", "little"):
            data = encode_bytes(signed, order)
            assert decode_bytes(data, order, width=width, signed=True) == signed


@pytest.mark.parametrize("width", range(1, 6))
@pytest.mark.parametrize("signed", [False, True])
def test_small_bitwise_and_arithmetic_match_integer_reference(width: int, signed: bool) -> None:
    modulus = 1 << width
    mask = modulus - 1
    minimum = -(modulus // 2) if signed else 0
    maximum = modulus // 2 - 1 if signed else mask
    for left_pattern in range(modulus):
        left = FixedWidthInteger.from_bit_pattern(left_pattern, width, signed)
        assert (~left).bit_pattern == mask - left_pattern
        for count in range(width + 2):
            assert (left << count).bit_pattern == (left_pattern * 2**count) % modulus
            assert (left >> count).value == left.value // 2**count
            assert left.logical_right_shift(count).bit_pattern == left_pattern // 2**count
        for right_pattern in range(modulus):
            right = FixedWidthInteger.from_bit_pattern(right_pattern, width, signed)
            assert (left & right).bit_pattern == left_pattern & right_pattern
            assert (left | right).bit_pattern == left_pattern | right_pattern
            assert (left ^ right).bit_pattern == left_pattern ^ right_pattern
            results = (
                (ArithmeticOperation.ADD, left.value + right.value),
                (ArithmeticOperation.SUBTRACT, left.value - right.value),
                (ArithmeticOperation.MULTIPLY, left.value * right.value),
            )
            for operation, exact in results:
                analysis = analyze_arithmetic(left, right, operation)
                assert analysis.exact_value == exact
                assert analysis.wrapped.bit_pattern == exact % modulus
                assert analysis.overflowed == (exact < minimum or exact > maximum)
                if analysis.overflowed:
                    with pytest.raises(IntegerRangeError):
                        _ = analysis.checked
                else:
                    assert analysis.checked.value == exact


@pytest.mark.parametrize("width", [7, 8, 9, 31, 32, 33, 64, 65, 128, 129])
def test_bytes_match_builtin_integer_serialization(width: int) -> None:
    mask = (1 << width) - 1
    for pattern in (0, 1, 1 << (width - 1), mask):
        value = FixedWidthInteger.from_bit_pattern(pattern, width, True)
        big = encode_bytes(value, "big")
        little = encode_bytes(value, "little")
        assert big == pattern.to_bytes((width + 7) // 8, "big")
        assert little == big[::-1]
        assert int.from_bytes(little, "little") == pattern
        assert decode_bytes(big, width=width, signed=True) == value
        assert value.resize(width + 8).value == value.value
        assert value.resize(width + 8).resize(width) == value


def test_ascii_bytes_and_integer_views_agree() -> None:
    text = "\x00RadixScope\n~\x7f"
    data = encode_ascii(text)
    value = decode_bytes(data)
    report = represent_bytes(value)
    assert report.data == data
    assert bytes.fromhex(report.hexadecimal) == data
    assert report.ascii_preview == ".RadixScope.~."
    assert decode_ascii(report.data) == text
    assert represent_bytes(value, "little").data == data[::-1]
