import pytest

from radixscope.core import (
    ByteOrder,
    FixedWidthInteger,
    IntegerRangeError,
    InvalidNumberError,
    decode_ascii,
    decode_bytes,
    encode_ascii,
    encode_bytes,
    integer_bounds,
    represent_bytes,
)


def test_endian_order_preserves_byte_count() -> None:
    value = FixedWidthInteger(0x004142, 24)
    assert encode_bytes(value) == bytes.fromhex("00 41 42")
    assert encode_bytes(value, ByteOrder.LITTLE) == bytes.fromhex("42 41 00")
    assert represent_bytes(value).hexadecimal == "00 41 42"
    assert represent_bytes(value).ascii_preview == ".AB"
    assert represent_bytes(value, "little").ascii_preview == "BA."


@pytest.mark.parametrize("width", [1, 5, 8, 9, 16, 32])
@pytest.mark.parametrize("order", [ByteOrder.BIG, ByteOrder.LITTLE])
def test_byte_round_trip_at_boundaries(width: int, order: ByteOrder) -> None:
    for signed in (False, True):
        minimum, maximum = integer_bounds(width, signed)
        for value in (minimum, 0, maximum):
            original = FixedWidthInteger(value, width, signed)
            data = encode_bytes(original, order)
            assert len(data) == (width + 7) // 8
            assert decode_bytes(data, order, width=width, signed=signed) == original


def test_signed_decode_uses_declared_bit_width() -> None:
    data = encode_bytes(FixedWidthInteger(-1, 5, True))
    assert data == bytes.fromhex("1F")
    assert decode_bytes(data, width=5, signed=True).value == -1
    assert decode_bytes(data, signed=True).value == 31
    assert decode_bytes(bytes.fromhex("FF"), signed=True).value == -1


def test_byte_padding_and_length_must_be_valid() -> None:
    with pytest.raises(IntegerRangeError):
        decode_bytes(bytes.fromhex("FF"), width=5)
    with pytest.raises(IntegerRangeError):
        decode_bytes(bytes.fromhex("01"), width=16)
    with pytest.raises(IntegerRangeError):
        decode_bytes(bytes.fromhex("00 01"), width=8)
    with pytest.raises(InvalidNumberError):
        decode_bytes(b"")


def test_ascii_codec_is_lossless_for_seven_bit_data() -> None:
    data = bytes(range(128))
    assert encode_ascii(decode_ascii(data)) == data
    assert decode_ascii(encode_ascii("RadixScope")) == "RadixScope"
    assert encode_ascii("") == b""
    assert decode_ascii(b"") == ""
    with pytest.raises(UnicodeEncodeError):
        encode_ascii("\uac00")
    with pytest.raises(UnicodeDecodeError):
        decode_ascii(bytes.fromhex("80"))


@pytest.mark.parametrize("order", ["middle", "BIG", "", True, 1])
def test_invalid_byte_order_is_rejected(order: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        encode_bytes(FixedWidthInteger(0, 8), order)
