import pytest

from radixscope.core import (
    BinaryExpression,
    ExactValue,
    InvalidExpressionError,
    LiteralExpression,
    TokenKind,
    UnaryExpression,
    evaluate_expression,
    evaluate_parsed_expression,
    parse_expression,
)


def test_parser_returns_a_reusable_tree() -> None:
    node = parse_expression("2#10 + 10#3 * 16#4")
    assert isinstance(node, BinaryExpression)
    assert node.operator is TokenKind.PLUS
    assert isinstance(node.left, LiteralExpression)
    assert node.left.value == ExactValue(2)
    assert isinstance(node.right, BinaryExpression)
    assert node.right.operator is TokenKind.MULTIPLY
    assert evaluate_parsed_expression(node) == ExactValue(14)
    assert evaluate_parsed_expression(node) == ExactValue(14)


def test_unary_minus_wraps_power() -> None:
    node = parse_expression("-10#2**10#2")
    assert isinstance(node, UnaryExpression)
    assert isinstance(node.operand, BinaryExpression)
    assert node.operand.operator is TokenKind.POWER


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("10#2**10#3**10#2", ExactValue(512)),
        ("-10#2**10#2", ExactValue(-4)),
        ("(-10#2)**10#2", ExactValue(4)),
        ("10#2**-10#3", ExactValue(1, 8)),
        ("10#2**-10#2**10#2", ExactValue(1, 16)),
        ("10#8/10#4/10#2", ExactValue(1)),
        ("10#0.(3)**10#2", ExactValue(1, 9)),
        ("10#0**10#0", ExactValue(1)),
    ],
)
def test_exact_power_and_associativity(expression: str, expected: ExactValue) -> None:
    assert evaluate_expression(expression) == expected


@pytest.mark.parametrize(
    "expression",
    ["10#4**(10#1/10#2)", "10#0**-10#1", "10#1/10#0", "10#2***10#3"],
)
def test_unsupported_power_and_arithmetic_failures(expression: str) -> None:
    with pytest.raises(InvalidExpressionError, match="position"):
        evaluate_expression(expression)


def test_excessive_nesting_raises_domain_error() -> None:
    with pytest.raises(InvalidExpressionError, match="nesting"):
        parse_expression("(" * 2000 + "10#1" + ")" * 2000)
