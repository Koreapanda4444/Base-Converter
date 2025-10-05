# converter/logic.py
from decimal import Decimal
from converter.utils import (
    set_decimal_context, sanitize_expr, tokenize, shunting_yard,
    is_digit_for_base, value_of_digit, DIGITS
)

def to_decimal(num_str: str, base_from: int):
    num_str = sanitize_expr(num_str)
    if "." in num_str:
        int_part, frac_part = num_str.split(".")
    else:
        int_part, frac_part = num_str, ""

    # 검증
    if int_part == "" and frac_part == "":
        raise ValueError("빈 숫자입니다.")
    if int_part and any(not is_digit_for_base(ch, base_from) for ch in int_part):
        raise ValueError(f"{base_from}진수에 맞지 않는 자리수가 포함되어 있습니다: {num_str}")
    if frac_part and any(not is_digit_for_base(ch, base_from) for ch in frac_part):
        raise ValueError(f"{base_from}진수에 맞지 않는 자리수가 포함되어 있습니다: {num_str}")

    # 정수부
    value = Decimal(0)
    for i, ch in enumerate(int_part[::-1]):
        if ch == "":
            continue
        d = value_of_digit(ch)
        value += d * (base_from ** i)

    # 소수부
    for i, ch in enumerate(frac_part, start=1):
        d = value_of_digit(ch)
        value += Decimal(d) / (base_from ** i)

    return value, [f"[to_decimal] {num_str} ({base_from}진) → {value}"]

def from_decimal(dec_val: Decimal, base_to: int, precision=12):
    # 정수부
    sign = "-" if dec_val < 0 else ""
    dec_abs = -dec_val if dec_val < 0 else dec_val
    int_part = int(dec_abs)
    frac_part = dec_abs - int_part

    digits = []
    if int_part == 0:
        digits.append("0")
    while int_part > 0:
        digits.append(DIGITS[int_part % base_to])
        int_part //= base_to
    digits.reverse()
    result = sign + ("".join(digits))

    # 소수부
    if frac_part > 0:
        result += "."
        f = frac_part
        for _ in range(precision):
            f *= base_to
            digit = int(f)
            result += DIGITS[digit]
            f -= digit
            if f == 0:
                break

    return result, [f"[from_decimal] {dec_val} → {result} ({base_to}진)"]

def _apply_unary(op: str, a: Decimal) -> Decimal:
    return a if op == "u+" else -a

def _apply_binary(op: str, a: Decimal, b: Decimal) -> Decimal:
    if op == "+": return a + b
    if op == "-": return a - b
    if op == "*": return a * b
    if op == "/":
        if b == 0:
            raise ZeroDivisionError("0으로 나눌 수 없습니다.")
        return a / b
    if op == "%":
        if b == 0:
            raise ZeroDivisionError("0으로 나눌 수 없습니다.")
        return a % b
    if op == "^": return a ** b
    raise ValueError(f"알 수 없는 연산자: {op}")

def evaluate_expression(expr: str, base_from: int, precision=12, round_mode="HALF_UP"):
    """
    안전 파서 기반 평가:
     - 토큰화 → 셔닝야드(RPN) → 스택 계산
     - 숫자 토큰은 모두 base_from 기준으로 해석
    """
    set_decimal_context(precision, round_mode)
    expr = sanitize_expr(expr)
    steps = [f"[evaluate] 식: {expr}"]

    # 1) 토큰화
    tokens = tokenize(expr, base_from)
    steps.append(f"[tokenize] {tokens}")

    # 2) 셔닝야드로 RPN
    rpn = shunting_yard(tokens)
    steps.append(f"[rpn] {rpn}")

    # 3) RPN 평가
    stack = []
    for t in rpn:
        if t in {"u+", "u-", "+", "-", "*", "/", "%", "^"}:
            if t in {"u+", "u-"}:
                if not stack:
                    raise ValueError("단항 연산 오류")
                a = stack.pop()
                stack.append(_apply_unary(t, a))
            else:
                if len(stack) < 2:
                    raise ValueError("이항 연산 피연산자 부족")
                b = stack.pop()
                a = stack.pop()
                stack.append(_apply_binary(t, a, b))
        else:
            # 숫자: base_from → 10진 Decimal
            val, _ = to_decimal(t, base_from)
            stack.append(val)

    if len(stack) != 1:
        raise ValueError("수식이 올바르지 않습니다.")
    result = stack[0]
    steps.append(f"[evaluate] 계산 결과: {result}")
    return result, steps

def convert(expr: str, base_from: int, base_to: int, precision=12, round_mode_str="HALF_UP"):
    set_decimal_context(precision, round_mode_str)
    expr = sanitize_expr(expr)
    if any(op in expr for op in "+-*/()%^"):
        dec, steps1 = evaluate_expression(expr, base_from, precision, round_mode_str)
    else:
        dec, steps1 = to_decimal(expr, base_from)
    out, steps2 = from_decimal(dec, base_to, precision)
    return out, steps1 + steps2
