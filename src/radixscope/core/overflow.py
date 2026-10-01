from dataclasses import dataclass
from enum import StrEnum

from radixscope.core.errors import IntegerRangeError
from radixscope.core.fixed_width import FixedWidthInteger, integer_bounds, validate_width


class ArithmeticOperation(StrEnum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"


@dataclass(frozen=True, slots=True)
class RangeAnalysis:
    exact_value: int
    width: int
    signed: bool
    minimum: int
    maximum: int
    wrapped: FixedWidthInteger

    @property
    def overflowed(self) -> bool:
        return not self.minimum <= self.exact_value <= self.maximum

    @property
    def checked(self) -> FixedWidthInteger:
        if self.overflowed:
            raise IntegerRangeError(
                f"{self.exact_value} is outside the range {self.minimum} through {self.maximum}"
            )
        return FixedWidthInteger(self.exact_value, self.width, self.signed)


def analyze_range(value: object, width: object, signed: bool = False) -> RangeAnalysis:
    checked_width = validate_width(width)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("value must be an integer")
    minimum, maximum = integer_bounds(checked_width, signed)
    pattern = value % (1 << checked_width)
    wrapped = FixedWidthInteger.from_bit_pattern(pattern, checked_width, signed)
    return RangeAnalysis(value, checked_width, signed, minimum, maximum, wrapped)


def analyze_arithmetic(
    left: FixedWidthInteger,
    right: FixedWidthInteger,
    operation: ArithmeticOperation,
) -> RangeAnalysis:
    if not isinstance(left, FixedWidthInteger) or not isinstance(right, FixedWidthInteger):
        raise TypeError("operands must be FixedWidthInteger values")
    if left.width != right.width or left.signed != right.signed:
        raise ValueError("operands must have the same width and signedness")
    if not isinstance(operation, ArithmeticOperation):
        raise TypeError("operation must be an ArithmeticOperation")
    if operation is ArithmeticOperation.ADD:
        exact_value = left.value + right.value
    elif operation is ArithmeticOperation.SUBTRACT:
        exact_value = left.value - right.value
    else:
        exact_value = left.value * right.value
    return analyze_range(exact_value, left.width, left.signed)
