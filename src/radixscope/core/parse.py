from radixscope.core.digits import digit_value, validate_base, validate_digits
from radixscope.core.errors import InvalidNumberError
from radixscope.core.value import ExactValue


def _normalized_text(text: str) -> str:
    if not isinstance(text, str):
        raise InvalidNumberError("number must be text")
    normalized = text.strip()
    if not normalized:
        raise InvalidNumberError("number cannot be empty")
    if any(character.isspace() for character in normalized):
        raise InvalidNumberError("internal whitespace is not allowed")
    return normalized


def _split_sign(text: str) -> tuple[int, str]:
    if text[0] == "+":
        return 1, text[1:]
    if text[0] == "-":
        return -1, text[1:]
    return 1, text


def _parse_unsigned_digits(digits: str, base: int) -> int:
    normalized_digits = validate_digits(digits, base)
    value = 0
    for digit in normalized_digits:
        value = value * base + digit_value(digit)
    return value


def parse_integer(text: str, base: object) -> ExactValue:
    checked_base = validate_base(base)
    sign, digits = _split_sign(_normalized_text(text))
    if not digits:
        raise InvalidNumberError("an integer requires at least one digit")
    return ExactValue(sign * _parse_unsigned_digits(digits, checked_base))


def parse_finite(text: str, base: object) -> ExactValue:
    checked_base = validate_base(base)
    sign, unsigned = _split_sign(_normalized_text(text))
    if unsigned.count(".") != 1:
        raise InvalidNumberError("a finite fraction requires one decimal point")
    integer_digits, fractional_digits = unsigned.split(".")
    if not integer_digits or not fractional_digits:
        raise InvalidNumberError("digits are required on both sides of the decimal point")
    integer_value = _parse_unsigned_digits(integer_digits, checked_base)
    fractional_value = _parse_unsigned_digits(fractional_digits, checked_base)
    denominator = checked_base ** len(fractional_digits)
    numerator = integer_value * denominator + fractional_value
    return ExactValue(sign * numerator, denominator)
