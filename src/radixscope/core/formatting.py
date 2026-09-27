from radixscope.core.digits import digit_char, validate_base
from radixscope.core.errors import NonIntegerValueError
from radixscope.core.value import ExactValue


def format_integer(value: ExactValue, base: object) -> str:
    checked_base = validate_base(base)
    if not isinstance(value, ExactValue):
        raise TypeError("value must be an ExactValue")
    if not value.is_integer:
        raise NonIntegerValueError("integer formatting requires an integer value")
    number = abs(value.numerator)
    if number == 0:
        return "0"
    digits: list[str] = []
    while number:
        number, remainder = divmod(number, checked_base)
        digits.append(digit_char(remainder))
    prefix = "-" if value.numerator < 0 else ""
    return prefix + "".join(reversed(digits))


def _fractional_expansion(
    remainder: int,
    denominator: int,
    base: int,
) -> tuple[list[str], list[str]]:
    digits: list[str] = []
    positions: dict[int, int] = {}
    while remainder:
        if remainder in positions:
            start = positions[remainder]
            return digits[:start], digits[start:]
        positions[remainder] = len(digits)
        remainder *= base
        digit, remainder = divmod(remainder, denominator)
        digits.append(digit_char(digit))
    return digits, []


def format_exact(value: ExactValue, base: object) -> str:
    checked_base = validate_base(base)
    if not isinstance(value, ExactValue):
        raise TypeError("value must be an ExactValue")
    if value.is_integer:
        return format_integer(value, checked_base)
    absolute_numerator = abs(value.numerator)
    integer_part, remainder = divmod(absolute_numerator, value.denominator)
    integer_text = format_integer(ExactValue(integer_part), checked_base)
    finite_digits, recurring_digits = _fractional_expansion(
        remainder,
        value.denominator,
        checked_base,
    )
    fractional_text = "".join(finite_digits)
    if recurring_digits:
        fractional_text += f"({''.join(recurring_digits)})"
    prefix = "-" if value.numerator < 0 else ""
    return f"{prefix}{integer_text}.{fractional_text}"
