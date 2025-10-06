# converter/logic.py
from __future__ import annotations
from decimal import Decimal
from fractions import Fraction
from typing import List, Tuple

from converter.utils import (
    set_decimal_context, sanitize_expr, tokenize, shunting_yard,
    is_digit_for_base, value_of_digit, DIGITS
)

# -----------------------------
# 내부 유틸: 정수부 변환
# -----------------------------
def _int_to_base_str(n: int, base: int) -> str:
    if n == 0:
        return "0"
    s = []
    x = n
    while x > 0:
        s.append(DIGITS[x % base])
        x //= base
    return "".join(reversed(s))

# -----------------------------
# 내부 유틸: Fraction → base 진수 문자열 (순환소수 표기)
#  - 정수부 + '.' + 소수부
#  - 순환 발견 시, 순환 구간을 괄호로 표기: 0.(3), 1.2(34) 등
#  - remainder 방문 위치를 기억하여 사이클 검출
# -----------------------------
def _fraction_to_base(fr: Fraction, base: int, precision: int = 12) -> Tuple[str, List[str]]:
    steps: List[str] = []
    if base < 2 or base > 36:
        raise ValueError("base must be 2..36")

    sign = "-" if fr < 0 else ""
    fr = -fr if fr < 0 else fr

    ip = fr.numerator // fr.denominator              # 정수부 (10진)
    rp = fr.numerator % fr.denominator               # 나머지 (소수부용)
    steps.append(f"[frac->base] input={fr} sign={'-' if sign else '+'}, int={ip}, rem={rp}/{fr.denominator}")

    int_part_str = _int_to_base_str(ip, base)

    if rp == 0:
        # 정확히 나누어 떨어지는 경우
        out = sign + int_part_str
        steps.append(f"[frac->base] exact integer → {out} ({base}진)")
        return out, steps

    # 소수부: long division in base, with cycle detection
    digits: List[str] = []
    seen = {}  # remainder -> index in digits
    cycle_start = None

    rem = rp
    den = fr.denominator
    idx = 0
    while rem != 0:
        if rem in seen:
            cycle_start = seen[rem]
            steps.append(f"[frac->base] repeat remainder={rem} at index={cycle_start}")
            break
        seen[rem] = idx

        rem *= base
        digit = rem // den
        rem = rem % den
        digits.append(DIGITS[int(digit)])
        idx += 1

        # 만약 순환이 없고 너무 길어지는 걸 방지: (precision이 안전 가드)
        # 순환이 감지되면 precision 제한을 무시하고 사이클 표기
        if cycle_start is None and idx >= max(precision, 1) and rem not in seen:
            # 반복이 없는 한도에서 precision만큼만 자름
            steps.append(f"[frac->base] reached precision (no cycle detected)")
            break

    if cycle_start is not None:
        # 순환 구간 괄호 표기
        nonrep = "".join(digits[:cycle_start])
        rep = "".join(digits[cycle_start:])
        frac_part = f"{nonrep}({rep})"
    else:
        frac_part = "".join(digits)

    out = f"{sign}{int_part_str}.{frac_part}"
    steps.append(f"[frac->base] out={out} ({base}진)")
    return out, steps

# -----------------------------
# 기존: 문자열을 base에서 10진 Decimal로
#  - 외부 호환을 위해 유지 (GUI 요약용)
#  - 내부 계산은 Fraction 기반으로 변경됨
# -----------------------------
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

# -----------------------------
# Fraction/Decimal → base 진수 문자열
#  - 내부는 Fraction 우선, Decimal이 오면 Fraction으로 변환 시도
# -----------------------------
def from_decimal(dec_val, base_to: int, precision=12):
    steps: List[str] = []
    if isinstance(dec_val, Fraction):
        fr = dec_val
        steps.append(f"[from_decimal] Fraction input={fr}")
    else:
        # Decimal/숫자 → Fraction 근사 (정밀도 내에서)
        try:
            s = str(dec_val)
            if "E" in s or "e" in s:
                # 과학 표기 들어오면 Decimal → str → Fraction(문자열)로
                fr = Fraction(s)
            else:
                # 소수점 문자열을 정확히 Fraction화
                fr = Fraction(s)
        except Exception:
            # 최후 수단: float 변환(권장X) — 가능한 피연산은 Fraction에서 들어오므로 거의 안씀
            fr = Fraction(float(dec_val))
        steps.append(f"[from_decimal] Decimal→Fraction: {fr}")

    out, st2 = _fraction_to_base(fr, base_to, precision=precision)
    steps.extend(st2)
    return out, steps

# -----------------------------
# 내부: 토큰을 Fraction 값으로 변환 (base_from 기준)
# -----------------------------
def _token_to_fraction(tok: str, base_from: int) -> Fraction:
    # "1A.F" 같은 숫자 토큰을 Fraction으로
    if "." in tok:
        int_part, frac_part = tok.split(".", 1)
    else:
        int_part, frac_part = tok, ""

    # 정수부
    val = 0
    for ch in int_part:
        if ch == "":
            continue
        if not is_digit_for_base(ch, base_from):
            raise ValueError(f"{base_from}진수에 맞지 않는 자리수가 포함되어 있습니다: {tok}")
        val = val * base_from + value_of_digit(ch)
    fr = Fraction(val, 1)

    # 소수부
    den = 1
    for ch in frac_part:
        if not is_digit_for_base(ch, base_from):
            raise ValueError(f"{base_from}진수에 맞지 않는 자리수가 포함되어 있습니다: {tok}")
        den *= base_from
        fr += Fraction(value_of_digit(ch), den)
    return fr

# -----------------------------
# 연산 적용 (Fraction)
# -----------------------------
def _apply_unary_frac(op: str, a: Fraction) -> Fraction:
    return a if op == "u+" else -a

def _apply_binary_frac(op: str, a: Fraction, b: Fraction) -> Fraction:
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
        # 분수 모듈러: a - floor(a/b)*b
        q = a // b  # 정수 나눗셈
        return a - q * b
    if op == "^":
        # 거듭제곱: 지수는 정수만 허용 (분수 지수는 정의 불명확)
        if b.denominator != 1:
            raise ValueError("분수 지수는 지원하지 않습니다.")
        n = b.numerator
        if n >= 0:
            return a ** n
        # 음의 지수도 허용 (a != 0)
        if a == 0:
            raise ZeroDivisionError("0의 음수 거듭제곱은 불가")
        return Fraction(1, 1) / (a ** (-n))
    raise ValueError(f"알 수 없는 연산자: {op}")

# -----------------------------
# 안전 파서 기반 평가 (Fraction)
# -----------------------------
def evaluate_expression(expr: str, base_from: int, precision=12, round_mode="HALF_UP"):
    """
    Fraction 기반 안전 평가:
     - 토큰화 → 셔닝야드(RPN) → 스택 계산(Fraction)
     - 최종 결과는 Fraction으로 유지
    """
    # Decimal 컨텍스트는 외부 호환을 위해 맞춰두지만, 실제 계산은 Fraction
    set_decimal_context(precision, round_mode)
    expr = sanitize_expr(expr)
    steps = [f"[evaluate] 식: {expr}"]

    # 1) 토큰화
    tokens = tokenize(expr, base_from)
    steps.append(f"[tokenize] {tokens}")

    # 2) RPN
    rpn = shunting_yard(tokens)
    steps.append(f"[rpn] {rpn}")

    # 3) RPN 평가 (Fraction)
    stack: List[Fraction] = []
    for t in rpn:
        if t in {"u+", "u-", "+", "-", "*", "/", "%", "^"}:
            if t in {"u+", "u-"}:
                if not stack:
                    raise ValueError("단항 연산 오류")
                a = stack.pop()
                stack.append(_apply_unary_frac(t, a))
            else:
                if len(stack) < 2:
                    raise ValueError("이항 연산 피연산자 부족")
                b = stack.pop()
                a = stack.pop()
                stack.append(_apply_binary_frac(t, a, b))
        else:
            stack.append(_token_to_fraction(t, base_from))

    if len(stack) != 1:
        raise ValueError("수식이 올바르지 않습니다.")
    result = stack[0]
    steps.append(f"[evaluate] 계산 결과(Fraction): {result.numerator}/{result.denominator}")
    return result, steps

# -----------------------------
# 외부 API: convert
#  - 연산이 있으면 Fraction 기반 평가 → 순환소수 표기 포함 변환
#  - 단순 숫자면 기존 경로도 허용 (외부 호환)
# -----------------------------
def convert(expr: str, base_from: int, base_to: int, precision=12, round_mode_str="HALF_UP"):
    set_decimal_context(precision, round_mode_str)
    expr = sanitize_expr(expr)

    # 연산 포함 여부
    if any(op in expr for op in "+-*/()%^"):
        fr, steps1 = evaluate_expression(expr, base_from, precision, round_mode_str)
        out, steps2 = from_decimal(fr, base_to, precision)  # Fraction 처리
        return out, steps1 + steps2
    else:
        # 순수 숫자 변환도 Fraction 경로로 정확도↑
        fr = _token_to_fraction(expr, base_from)
        steps1 = [f"[to_fraction] {expr} ({base_from}진) → {fr.numerator}/{fr.denominator}"]
        out, steps2 = from_decimal(fr, base_to, precision)
        return out, steps1 + steps2
