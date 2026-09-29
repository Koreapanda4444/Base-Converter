from dataclasses import dataclass

from radixscope.core.errors import IntegerRangeError, InvalidWidthError


def validate_width(width: object) -> int:
    if isinstance(width, bool) or not isinstance(width, int):
        raise InvalidWidthError("width must be an integer")
    if width < 1:
        raise InvalidWidthError("width must be at least one bit")
    return width


def integer_bounds(width: object, signed: bool = False) -> tuple[int, int]:
    checked_width = validate_width(width)
    if not isinstance(signed, bool):
        raise TypeError("signed must be a boolean")
    if signed:
        limit = 1 << (checked_width - 1)
        return -limit, limit - 1
    return 0, (1 << checked_width) - 1


@dataclass(frozen=True, slots=True)
class FixedWidthInteger:
    value: int
    width: int
    signed: bool = False

    def __post_init__(self) -> None:
        checked_width = validate_width(self.width)
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise TypeError("value must be an integer")
        if not isinstance(self.signed, bool):
            raise TypeError("signed must be a boolean")
        minimum, maximum = integer_bounds(checked_width, self.signed)
        if not minimum <= self.value <= maximum:
            kind = "signed" if self.signed else "unsigned"
            raise IntegerRangeError(
                f"{self.value} is outside the {checked_width}-bit {kind} range "
                f"{minimum} through {maximum}"
            )
        object.__setattr__(self, "width", checked_width)

    @property
    def minimum(self) -> int:
        return integer_bounds(self.width, self.signed)[0]

    @property
    def maximum(self) -> int:
        return integer_bounds(self.width, self.signed)[1]

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def is_negative(self) -> bool:
        return self.value < 0

    @property
    def bit_pattern(self) -> int:
        return self.value % self.modulus

    @property
    def bits(self) -> str:
        return format(self.bit_pattern, f"0{self.width}b")

    @classmethod
    def from_bit_pattern(
        cls,
        pattern: object,
        width: object,
        signed: bool = False,
    ) -> "FixedWidthInteger":
        checked_width = validate_width(width)
        if isinstance(pattern, bool) or not isinstance(pattern, int):
            raise TypeError("bit pattern must be an integer")
        if not isinstance(signed, bool):
            raise TypeError("signed must be a boolean")
        maximum = (1 << checked_width) - 1
        if not 0 <= pattern <= maximum:
            raise IntegerRangeError(
                f"bit pattern must be between 0 and {maximum} for width {checked_width}"
            )
        sign_bit = 1 << (checked_width - 1)
        value = pattern - (1 << checked_width) if signed and pattern & sign_bit else pattern
        return cls(value, checked_width, signed)

    def reinterpret(self, signed: bool) -> "FixedWidthInteger":
        return self.from_bit_pattern(self.bit_pattern, self.width, signed)


def encode_twos_complement(value: object, width: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("value must be an integer")
    return FixedWidthInteger(value, validate_width(width), signed=True).bit_pattern


def decode_twos_complement(pattern: object, width: object) -> int:
    return FixedWidthInteger.from_bit_pattern(pattern, width, signed=True).value


def format_twos_complement(value: object, width: object) -> str:
    checked_width = validate_width(width)
    return format(encode_twos_complement(value, checked_width), f"0{checked_width}b")


def parse_twos_complement(bits: str) -> FixedWidthInteger:
    if not isinstance(bits, str):
        raise TypeError("bits must be text")
    if not bits:
        raise ValueError("bits cannot be empty")
    if any(bit not in "01" for bit in bits):
        raise ValueError("bits can contain only zero and one")
    return FixedWidthInteger.from_bit_pattern(int(bits, 2), len(bits), signed=True)
