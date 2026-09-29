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
