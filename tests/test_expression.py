import pytest

from radixscope.core import ExactValue, InvalidExpressionError, evaluate_expression


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2#101 + 16#A", ExactValue(15)),
        ("16#A.F - 2#0.11", ExactValue(163, 16)),
        ("10#0.(3) * 8#30", ExactValue(8)),
        ("(2#101 + 16#B) / 8#20", ExactValue(1)),
        ("-2#101 + +10#2", ExactValue(-3)),
        ("2#10 + 10#3 * 16#4", ExactValue(14)),
    ],
)
def test_evaluate_mixed_base_expression(expression: str, expected: ExactValue) -> None:
    assert evaluate_expression(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "10",
        "2#2 + 10#1",
        "10#1 / 2#0",
        "(2#1 + 8#1",
        "2#1 +",
        "16#A.$",
        "10#0.()",
    ],
)
def test_invalid_mixed_base_expression(expression: str) -> None:
    with pytest.raises(InvalidExpressionError):
        evaluate_expression(expression)
