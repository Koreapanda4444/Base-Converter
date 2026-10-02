import struct
from dataclasses import dataclass
from enum import IntEnum, StrEnum

from radixscope.core.fixed_width import FixedWidthInteger
from radixscope.core.representations import ByteOrder, decode_bytes, encode_bytes
from radixscope.core.value import ExactValue


class IEEEFormat(IntEnum):
    BINARY32 = 32
    BINARY64 = 64

    @property
    def fraction_width(self) -> int:
        return 23 if self is IEEEFormat.BINARY32 else 52

    @property
    def exponent_width(self) -> int:
        return 8 if self is IEEEFormat.BINARY32 else 11

    @property
    def bias(self) -> int:
        return (1 << (self.exponent_width - 1)) - 1


class FloatClass(StrEnum):
    ZERO = "zero"
    SUBNORMAL = "subnormal"
    NORMAL = "normal"
    INFINITY = "infinity"
    NAN = "nan"


def _validate_format(width: object) -> IEEEFormat:
    if isinstance(width, bool) or not isinstance(width, int):
        raise TypeError("IEEE format must be 32 or 64")
    try:
        return IEEEFormat(width)
    except ValueError as error:
        raise ValueError("IEEE format must be 32 or 64") from error


@dataclass(frozen=True, slots=True)
class IEEE754Value:
    pattern: int
    format: IEEEFormat

    def __post_init__(self) -> None:
        checked_format = _validate_format(self.format)
        FixedWidthInteger.from_bit_pattern(self.pattern, checked_format.value)
        object.__setattr__(self, "format", checked_format)

    @property
    def sign_bit(self) -> int:
        return self.pattern >> (self.format.value - 1)

    @property
    def exponent_bits(self) -> int:
        mask = (1 << self.format.exponent_width) - 1
        return (self.pattern >> self.format.fraction_width) & mask

    @property
    def fraction_bits(self) -> int:
        return self.pattern & ((1 << self.format.fraction_width) - 1)

    @property
    def classification(self) -> FloatClass:
        if self.exponent_bits == (1 << self.format.exponent_width) - 1:
            return FloatClass.NAN if self.fraction_bits else FloatClass.INFINITY
        if self.exponent_bits == 0:
            return FloatClass.SUBNORMAL if self.fraction_bits else FloatClass.ZERO
        return FloatClass.NORMAL

    @property
    def exponent(self) -> int | None:
        if self.classification in (FloatClass.INFINITY, FloatClass.NAN):
            return None
        return (self.exponent_bits or 1) - self.format.bias

    @property
    def significand(self) -> ExactValue | None:
        if self.exponent is None:
            return None
        leading = 1 << self.format.fraction_width if self.exponent_bits else 0
        return ExactValue(leading + self.fraction_bits, 1 << self.format.fraction_width)

    @property
    def exact(self) -> ExactValue | None:
        exponent = self.exponent
        significand = self.significand
        if exponent is None or significand is None:
            return None
        if exponent >= 0:
            value = significand * ExactValue(1 << exponent)
        else:
            value = significand / ExactValue(1 << -exponent)
        return -value if self.sign_bit else value

    @property
    def is_quiet_nan(self) -> bool:
        quiet_bit = 1 << (self.format.fraction_width - 1)
        return self.classification is FloatClass.NAN and bool(self.fraction_bits & quiet_bit)

    @property
    def nan_payload(self) -> int | None:
        if self.classification is not FloatClass.NAN:
            return None
        return self.fraction_bits & ((1 << (self.format.fraction_width - 1)) - 1)

    @property
    def bits(self) -> str:
        return format(self.pattern, f"0{self.format.value}b")

    @property
    def hexadecimal(self) -> str:
        return format(self.pattern, f"0{self.format.value // 4}X")

    def to_bytes(self, byteorder: object = ByteOrder.BIG) -> bytes:
        return encode_bytes(FixedWidthInteger(self.pattern, self.format.value), byteorder)

    def to_float(self) -> float:
        code = ">f" if self.format is IEEEFormat.BINARY32 else ">d"
        result: float = struct.unpack(code, self.to_bytes())[0]
        return result


def decode_ieee754(pattern: object, width: object = IEEEFormat.BINARY64) -> IEEE754Value:
    checked_format = _validate_format(width)
    value = FixedWidthInteger.from_bit_pattern(pattern, checked_format.value)
    return IEEE754Value(value.bit_pattern, checked_format)


def decode_ieee754_bytes(
    data: bytes,
    width: object = IEEEFormat.BINARY64,
    byteorder: object = ByteOrder.BIG,
) -> IEEE754Value:
    checked_format = _validate_format(width)
    value = decode_bytes(data, byteorder, width=checked_format.value)
    return IEEE754Value(value.bit_pattern, checked_format)
