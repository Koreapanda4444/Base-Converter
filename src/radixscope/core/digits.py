from radixscope.core.errors import InvalidBaseError, InvalidDigitError

DIGIT_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MIN_BASE = 2
MAX_BASE = len(DIGIT_ALPHABET)


def validate_base(base: object) -> int:
    if isinstance(base, bool) or not isinstance(base, int):
        raise InvalidBaseError("base must be an integer")
    if not MIN_BASE <= base <= MAX_BASE:
        raise InvalidBaseError(f"base must be between {MIN_BASE} and {MAX_BASE}")
    return base


def digit_value(digit: str) -> int:
    if len(digit) != 1:
        raise InvalidDigitError("a digit must contain exactly one character")
    value = DIGIT_ALPHABET.find(digit.upper())
    if value < 0:
        raise InvalidDigitError(f"unsupported digit: {digit!r}")
    return value


def digit_char(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidDigitError("digit value must be an integer")
    if not 0 <= value < len(DIGIT_ALPHABET):
        raise InvalidDigitError("digit value must be between 0 and 35")
    return DIGIT_ALPHABET[value]


def validate_digit(digit: str, base: object) -> int:
    checked_base = validate_base(base)
    value = digit_value(digit)
    if value >= checked_base:
        raise InvalidDigitError(f"digit {digit!r} is invalid in base {checked_base}")
    return value


def validate_digits(text: str, base: object) -> str:
    checked_base = validate_base(base)
    if not text:
        raise InvalidDigitError("at least one digit is required")
    for digit in text:
        validate_digit(digit, checked_base)
    return text.upper()
