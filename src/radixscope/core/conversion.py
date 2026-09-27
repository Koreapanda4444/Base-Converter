from collections.abc import Iterable

from radixscope.core.digits import validate_base
from radixscope.core.formatting import RoundingMode, format_value
from radixscope.core.parse import parse_number
from radixscope.core.value import ExactValue


def convert_bases(
    value: ExactValue,
    bases: Iterable[object],
    precision: object | None = None,
    rounding: RoundingMode = RoundingMode.HALF_EVEN,
) -> dict[int, str]:
    if not isinstance(value, ExactValue):
        raise TypeError("value must be an ExactValue")
    results: dict[int, str] = {}
    for base in bases:
        checked_base = validate_base(base)
        if checked_base in results:
            raise ValueError(f"duplicate target base: {checked_base}")
        results[checked_base] = format_value(value, checked_base, precision, rounding)
    if not results:
        raise ValueError("at least one target base is required")
    return results


def convert_text(
    text: str,
    source_base: object,
    target_bases: Iterable[object],
    precision: object | None = None,
    rounding: RoundingMode = RoundingMode.HALF_EVEN,
) -> dict[int, str]:
    value = parse_number(text, source_base)
    return convert_bases(value, target_bases, precision, rounding)
