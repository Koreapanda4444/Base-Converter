# converter/logic.py
from decimal import Decimal
from converter.utils import set_decimal_context, sanitize_expr

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def to_decimal(num_str: str, base_from: int):
    num_str = sanitize_expr(num_str)
    if "." in num_str:
        int_part, frac_part = num_str.split(".")
    else:
        int_part, frac_part = num_str, ""

    value = Decimal(0)
    for i, ch in enumerate(int_part[::-1]):
        value += DIGITS.index(ch) * (base_from ** i)
    for i, ch in enumerate(frac_part, start=1):
        value += DIGITS.index(ch) / (base_from ** i)
    return value, [f"[to_decimal] {num_str} ({base_from}진) → {value}"]

def from_decimal(dec_val: Decimal, base_to: int, precision=12):
    int_part = int(dec_val)
    frac_part = dec_val - int_part
    digits = []

    if int_part == 0:
        digits.append("0")
    while int_part > 0:
        digits.append(DIGITS[int_part % base_to])
        int_part //= base_to
    digits.reverse()
    result = "".join(digits)

    if frac_part > 0:
        result += "."
        for _ in range(precision):
            frac_part *= base_to
            digit = int(frac_part)
            result += DIGITS[digit]
            frac_part -= digit
            if frac_part == 0:
                break
    return result, [f"[from_decimal] {dec_val} → {result} ({base_to}진)"]

def evaluate_expression(expr: str, base_from: int, precision=12, round_mode="HALF_UP"):
    set_decimal_context(precision, round_mode)
    expr = sanitize_expr(expr)
    steps = [f"[evaluate] 식: {expr}"]
    for ch in expr:
        if ch not in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.+-*/()":
            raise ValueError("잘못된 문자 포함")
    try:
        replaced = ""
        token = ""
        for ch in expr + " ":
            if ch in DIGITS or ch == ".":
                token += ch
            else:
                if token:
                    val, _ = to_decimal(token, base_from)
                    replaced += str(val)
                    token = ""
                replaced += ch
        result = Decimal(eval(replaced))
        steps.append(f"[evaluate] 계산 결과: {result}")
        return result, steps
    except Exception as e:
        raise ValueError(f"수식 오류: {e}")

def convert(expr: str, base_from: int, base_to: int, precision=12, round_mode_str="HALF_UP"):
    set_decimal_context(precision, round_mode_str)
    expr = sanitize_expr(expr)
    if any(op in expr for op in "+-*/()"):
        dec, steps1 = evaluate_expression(expr, base_from, precision, round_mode_str)
    else:
        dec, steps1 = to_decimal(expr, base_from)
    out, steps2 = from_decimal(dec, base_to, precision)
    return out, steps1 + steps2
