from radixscope.core.digits import validate_base
from radixscope.core.errors import InvalidBaseError, InvalidNumberError
from radixscope.core.parse import parse_number
from radixscope.core.value import ExactValue

_PREFIX_BASES = {"0b": 2, "0o": 8, "0x": 16}
_DECIMAL_DIGITS = "0123456789"


def parse_literal(text: str) -> ExactValue:
    if not isinstance(text, str):
        raise InvalidNumberError("literal must be text")
    normalized = text.strip()
    if not normalized:
        raise InvalidNumberError("literal cannot be empty")
    if any(character.isspace() for character in normalized):
        raise InvalidNumberError("internal whitespace is not allowed in a literal")
    sign = ""
    unsigned = normalized
    if unsigned[0] in "+-":
        sign, unsigned = unsigned[0], unsigned[1:]
    if "/" in unsigned:
        raise InvalidNumberError("use the division operator for ratios between literals")
    if "#" in unsigned:
        if unsigned.count("#") != 1:
            raise InvalidNumberError("a literal requires exactly one base separator")
        base_text, numeral = unsigned.split("#")
        if not base_text or any(digit not in _DECIMAL_DIGITS for digit in base_text):
            raise InvalidBaseError("literal base must contain only decimal digits")
        base_text = base_text.lstrip("0") or "0"
        if len(base_text) > 2:
            raise InvalidBaseError("literal base must be between 2 and 36")
        base = validate_base(int(base_text))
    elif unsigned[:2].lower() in _PREFIX_BASES:
        base = _PREFIX_BASES[unsigned[:2].lower()]
        numeral = unsigned[2:]
    else:
        base, numeral = 10, unsigned
    if not numeral or numeral[0] in "+-":
        raise InvalidNumberError("a literal requires digits after its base prefix")
    return parse_number(sign + numeral, base)
