import pytest

from radixscope.core import (
    ExactValue,
    InvalidExpressionError,
    RadixScopeError,
    evaluate_expression,
    format_integer,
    parse_literal,
    tokenize_expression,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0xFF", ExactValue(255)),
        ("  -0Xff ", ExactValue(-255)),
        ("+0b101", ExactValue(5)),
        ("0O17", ExactValue(15)),
        ("16#A.F", ExactValue(175, 16)),
        ("0xA.F", ExactValue(175, 16)),
        ("0b0.(01)", ExactValue(1, 3)),
        ("0o0.4", ExactValue(1, 2)),
        ("0x0.(5)", ExactValue(1, 3)),
        ("36#Z", ExactValue(35)),
        ("00016#ff", ExactValue(255)),
        ("123", ExactValue(123)),
        ("-1.25", ExactValue(-5, 4)),
        ("0.1(6)", ExactValue(1, 6)),
    ],
)
def test_parse_numeric_literal(text: str, expected: ExactValue) -> None:
    assert parse_literal(text) == expected


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("0xFF + 0b10", ExactValue(257)),
        ("16#FF + 2#10", ExactValue(257)),
        ("0xA.F - 2#0.11", ExactValue(163, 16)),
        ("0b0.(01) + 0.(3)", ExactValue(2, 3)),
        ("0O17 - 10", ExactValue(5)),
        ("36#Z / 0xA", ExactValue(7, 2)),
        ("(0x10 + 2#10) ** -2", ExactValue(1, 324)),
        ("0b1 / 0b10", ExactValue(1, 2)),
    ],
)
def test_mixed_literal_expression(expression: str, expected: ExactValue) -> None:
    assert evaluate_expression(expression) == expected


def test_base_label_round_trip() -> None:
    for base in range(2, 37):
        digits = format_integer(ExactValue(123456789), base)
        assert parse_literal(f"{base}#{digits}") == ExactValue(123456789)


def test_tokenizer_preserves_literal_spellings() -> None:
    expression = "0Xff + 2#10 + 0.1(6)"
    tokens = tokenize_expression(expression)
    assert [token.text for token in tokens] == ["0Xff", "+", "2#10", "+", "0.1(6)", ""]
    for token in tokens:
        assert expression[token.position : token.end] == token.text


@pytest.mark.parametrize(
    "text",
    ["0x", "0b2", "0o8", "16#G", "1#0", "37#1", "2#-1", "0 xFF", "16##A", "1/2"],
)
def test_invalid_literals(text: str) -> None:
    with pytest.raises(RadixScopeError):
        parse_literal(text)


@pytest.mark.parametrize("expression", ["0x", "0b2 + 1", "0xA 0b1", "0x1.()", "0x1p2"])
def test_literal_errors_in_expressions(expression: str) -> None:
    with pytest.raises(InvalidExpressionError, match="position"):
        evaluate_expression(expression)
