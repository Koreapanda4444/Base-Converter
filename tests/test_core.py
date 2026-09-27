import pytest

from radixscope.core import (
    ExactValue,
    InvalidBaseError,
    InvalidDigitError,
    InvalidNumberError,
    parse_number,
    validate_base,
    validate_digits,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (ExactValue(2, 4), ExactValue(1, 2)),
        (ExactValue(-2, -4), ExactValue(1, 2)),
        (ExactValue(0, -5), ExactValue(0)),
    ],
)
def test_exact_value_normalization(value: ExactValue, expected: ExactValue) -> None:
    assert value == expected


@pytest.mark.parametrize(
    ("text", "base", "expected"),
    [
        ("-101", 2, ExactValue(-5)),
        ("A.F", 16, ExactValue(175, 16)),
        ("A/10", 16, ExactValue(5, 8)),
        ("0.(3)", 10, ExactValue(1, 3)),
        ("0.1(6)", 10, ExactValue(1, 6)),
        ("0.(01)", 2, ExactValue(1, 3)),
        ("1.(9)", 10, ExactValue(2)),
    ],
)
def test_parse_number(text: str, base: int, expected: ExactValue) -> None:
    assert parse_number(text, base) == expected


@pytest.mark.parametrize("base", [1, 37, True, 2.5])
def test_invalid_base(base: object) -> None:
    with pytest.raises(InvalidBaseError):
        validate_base(base)


@pytest.mark.parametrize(
    ("text", "base", "error"),
    [
        ("", 10, InvalidNumberError),
        ("-", 10, InvalidNumberError),
        ("1 0", 10, InvalidNumberError),
        ("2", 2, InvalidDigitError),
        ("1.", 10, InvalidNumberError),
        ("1/0", 10, InvalidNumberError),
        ("0.()", 10, InvalidNumberError),
        ("0.(3", 10, InvalidNumberError),
        ("0.(2)", 2, InvalidDigitError),
    ],
)
def test_invalid_number(text: str, base: int, error: type[ValueError]) -> None:
    with pytest.raises(error):
        parse_number(text, base)


def test_digit_normalization() -> None:
    assert validate_digits("aF01", 16) == "AF01"
