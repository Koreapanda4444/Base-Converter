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


def parse_integer(text: str, base: object) -> ExactValue:
    checked_base = validate_base(base)
    sign, digits = _split_sign(_normalized_text(text))
    if not digits:
        raise InvalidNumberError("an integer requires at least one digit")
    normalized_digits = validate_digits(digits, checked_base)
    value = 0
    for digit in normalized_digits:
        value = value * checked_base + digit_value(digit)
    return ExactValue(sign * value)
