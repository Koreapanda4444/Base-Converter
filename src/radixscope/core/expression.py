from radixscope.core.errors import InvalidExpressionError, RadixScopeError
from radixscope.core.parse import parse_number
from radixscope.core.tokenize import ExpressionToken, tokenize_expression
from radixscope.core.value import ExactValue


class _ExpressionParser:
    def __init__(self, expression: str) -> None:
        self.tokens = tokenize_expression(expression)
        self.position = 0

    @property
    def current(self) -> ExpressionToken:
        return self.tokens[self.position]

    def advance(self) -> ExpressionToken:
        token = self.current
        self.position += 1
        return token

    def parse(self) -> ExactValue:
        if self.current.kind == "end":
            raise InvalidExpressionError("expression cannot be empty")
        value = self.parse_expression()
        if self.current.kind != "end":
            raise InvalidExpressionError(
                f"unexpected token {self.current.text!r} at position {self.current.position}"
            )
        return value

    def parse_expression(self) -> ExactValue:
        value = self.parse_term()
        while self.current.kind in {"+", "-"}:
            operator = self.advance().kind
            operand = self.parse_term()
            value = value + operand if operator == "+" else value - operand
        return value

    def parse_term(self) -> ExactValue:
        value = self.parse_factor()
        while self.current.kind in {"*", "/"}:
            operator = self.advance().kind
            operand = self.parse_factor()
            if operator == "*":
                value = value * operand
            else:
                try:
                    value = value / operand
                except ZeroDivisionError as error:
                    raise InvalidExpressionError("division by zero") from error
        return value

    def parse_factor(self) -> ExactValue:
        if self.current.kind == "+":
            self.advance()
            return self.parse_factor()
        if self.current.kind == "-":
            self.advance()
            return -self.parse_factor()
        return self.parse_primary()

    def parse_primary(self) -> ExactValue:
        token = self.current
        if token.kind == "literal":
            self.advance()
            base_text, numeral = token.text.split("#", 1)
            try:
                return parse_number(numeral, int(base_text))
            except RadixScopeError as error:
                raise InvalidExpressionError(
                    f"invalid literal {token.text!r} at position {token.position}: {error}"
                ) from error
        if token.kind == "(":
            self.advance()
            value = self.parse_expression()
            if self.current.kind != ")":
                raise InvalidExpressionError(
                    f"missing closing parenthesis at position {token.position}"
                )
            self.advance()
            return value
        if token.kind == "end":
            raise InvalidExpressionError("unexpected end of expression")
        raise InvalidExpressionError(
            f"expected a literal or parenthesis at position {token.position}"
        )


def evaluate_expression(expression: str) -> ExactValue:
    return _ExpressionParser(expression).parse()
