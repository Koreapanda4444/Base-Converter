from fractions import Fraction
from typing import cast

import pytest

from radixscope.core import ExactValue, InvalidExpressionError, evaluate_expression


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1 + 2 * 3 ** 2", Fraction(19)),
        ("(1 + 2) * 3 ** 2", Fraction(27)),
        ("(1 + 2 * 3) ** 2", Fraction(49)),
        ("8 - 3 - 2", Fraction(3)),
        ("8 / 4 * 2", Fraction(4)),
        ("16 / (4 * 2)", Fraction(2)),
        ("-2 ** 2 + 3", Fraction(-1)),
        ("(-2) ** 2 + 3", Fraction(7)),
        ("2 ** 3 ** 2", Fraction(512)),
        ("(2 ** 3) ** 2", Fraction(64)),
        ("2 ** -3 ** 2", Fraction(1, 512)),
        ("--2 + -+-3", Fraction(5)),
        ("0x10 / 0b11 + 36#Z / 7", Fraction(31, 3)),
        ("(0.(3) + 0b0.(01)) * 1.5", Fraction(1)),
        ("0.1 + 0.2 - 0.3", Fraction(0)),
        (" 0xA\n+\t(2#10 / 0o4) ", Fraction(21, 2)),
    ],
)
def test_precedence_against_rational_reference(expression: str, expected: Fraction) -> None:
    assert evaluate_expression(expression) == ExactValue.from_fraction(expected)


@pytest.mark.parametrize(
    "expression",
    [
        "1 + * 2",
        "1 **",
        "1 // 2",
        "1 % 2",
        "1 ^ 2",
        "()",
        "(1 + 2))",
        "(1 + 2",
        "2(3)",
        "0x1 0b1",
        "16 #FF",
        "0 xFF",
        "1.2(3)(4)",
        "1 = 2",
        "x + 1",
        "abs(-1)",
        "1;2",
        "0xF.FF / (1 - 1)",
        "0 ** (1 - 2)",
        "2 ** (1 / 2)",
    ],
)
def test_failures_use_expression_error_with_position(expression: str) -> None:
    with pytest.raises(InvalidExpressionError, match="position"):
        evaluate_expression(expression)


@pytest.mark.parametrize("expression", [None, 10, True, ["1", "+", "2"]])
def test_nontext_expression_is_rejected(expression: object) -> None:
    with pytest.raises(InvalidExpressionError, match="text"):
        evaluate_expression(cast(str, expression))


def test_error_position_uses_original_source() -> None:
    with pytest.raises(InvalidExpressionError, match="position 8"):
        evaluate_expression("  0xA + 2#2")
