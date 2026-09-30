import pytest

from radixscope.core import ExpressionToken, InvalidExpressionError, TokenKind, tokenize_expression


def test_tokens_keep_source_spans() -> None:
    expression = " 16#A + (2#11) "
    tokens = tokenize_expression(expression)
    assert [token.kind for token in tokens] == [
        TokenKind.LITERAL,
        TokenKind.PLUS,
        TokenKind.LEFT_PAREN,
        TokenKind.LITERAL,
        TokenKind.RIGHT_PAREN,
        TokenKind.END,
    ]
    assert tokens[0] == ExpressionToken(TokenKind.LITERAL, "16#A", 1, 5)
    assert tokens[-1].position == len(expression)
    for token in tokens:
        assert expression[token.position : token.end] == token.text


def test_recurring_parentheses_stay_in_literal() -> None:
    tokens = tokenize_expression("(10#0.1(6) + 2#0.(01))")
    assert [token.text for token in tokens] == ["(", "10#0.1(6)", "+", "2#0.(01)", ")", ""]


def test_power_is_one_token_and_sign_is_separate() -> None:
    tokens = tokenize_expression("-2#10**+10#3 * 8#2 / 10#4")
    assert [token.kind for token in tokens] == [
        TokenKind.MINUS,
        TokenKind.LITERAL,
        TokenKind.POWER,
        TokenKind.PLUS,
        TokenKind.LITERAL,
        TokenKind.MULTIPLY,
        TokenKind.LITERAL,
        TokenKind.DIVIDE,
        TokenKind.LITERAL,
        TokenKind.END,
    ]


@pytest.mark.parametrize(
    "expression", ["2#", "10#0.()", "10#1.", "\uff12#1", "16#\uff21", "x", "2#1;"]
)
def test_malformed_tokens_raise_domain_error(expression: str) -> None:
    with pytest.raises(InvalidExpressionError, match="position"):
        tokenize_expression(expression)


def test_empty_input_has_only_end_token() -> None:
    assert tokenize_expression("") == (ExpressionToken(TokenKind.END, "", 0, 0),)
