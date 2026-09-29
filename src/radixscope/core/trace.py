from dataclasses import dataclass

from radixscope.core.digits import digit_char, validate_base
from radixscope.core.formatting import format_exact
from radixscope.core.parse import parse_number
from radixscope.core.value import ExactValue


@dataclass(frozen=True, slots=True)
class IntegerDivisionStep:
    dividend: int
    divisor: int
    quotient: int
    remainder: int
    digit: str


@dataclass(frozen=True, slots=True)
class FractionMultiplicationStep:
    position: int
    remainder: int
    multiplier: int
    product: int
    digit_value: int
    digit: str
    next_remainder: int


@dataclass(frozen=True, slots=True)
class ConversionTrace:
    value: ExactValue
    base: int
    sign: int
    integer_steps: tuple[IntegerDivisionStep, ...]
    fractional_steps: tuple[FractionMultiplicationStep, ...]
    recurring_start: int | None
    result: str

    @property
    def terminates(self) -> bool:
        return self.recurring_start is None


def _trace_integer(number: int, base: int) -> tuple[IntegerDivisionStep, ...]:
    if number == 0:
        return (IntegerDivisionStep(0, base, 0, 0, "0"),)
    steps: list[IntegerDivisionStep] = []
    dividend = number
    while dividend:
        quotient, remainder = divmod(dividend, base)
        steps.append(
            IntegerDivisionStep(
                dividend,
                base,
                quotient,
                remainder,
                digit_char(remainder),
            )
        )
        dividend = quotient
    return tuple(steps)


def _trace_fraction(
    remainder: int,
    denominator: int,
    base: int,
) -> tuple[tuple[FractionMultiplicationStep, ...], int | None]:
    positions: dict[int, int] = {}
    steps: list[FractionMultiplicationStep] = []
    while remainder:
        if remainder in positions:
            return tuple(steps), positions[remainder]
        positions[remainder] = len(steps)
        product = remainder * base
        value, next_remainder = divmod(product, denominator)
        steps.append(
            FractionMultiplicationStep(
                len(steps),
                remainder,
                base,
                product,
                value,
                digit_char(value),
                next_remainder,
            )
        )
        remainder = next_remainder
    return tuple(steps), None


def trace_value(value: ExactValue, base: object) -> ConversionTrace:
    checked_base = validate_base(base)
    if not isinstance(value, ExactValue):
        raise TypeError("value must be an ExactValue")
    absolute_numerator = abs(value.numerator)
    integer_part, remainder = divmod(absolute_numerator, value.denominator)
    fractional_steps, recurring_start = _trace_fraction(
        remainder,
        value.denominator,
        checked_base,
    )
    return ConversionTrace(
        value,
        checked_base,
        value.sign,
        _trace_integer(integer_part, checked_base),
        fractional_steps,
        recurring_start,
        format_exact(value, checked_base),
    )


def trace_text(text: str, source_base: object, target_base: object) -> ConversionTrace:
    return trace_value(parse_number(text, source_base), target_base)
