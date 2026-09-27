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
