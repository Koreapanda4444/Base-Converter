import re
from decimal import Decimal, getcontext
from .utils import DIGITS, digval, sanitize, split_tokens, is_operator, is_valid_for_base

getcontext().prec = 100  # 충분한 정밀도

def to_decimal(s: str, base: int):
    """문자열 s(부호/소수점 포함)를 10진 Decimal로 변환. (정밀 변환)"""
    s = sanitize(s)
    if not is_valid_for_base(s, base):
        raise ValueError(f"입력이 {base}진법에 유효하지 않음: {s}" )

    sign = 1
    if s.startswith('-'):
        sign = -1
        s = s[1:]
    if '.' in s:
        intp, frac = s.split('.', 1)
    else:
        intp, frac = s, ""

    # 정수부
    val = Decimal(0)
    for ch in intp:
        if ch == "": continue
        v = digval(ch)
        val = val * base + v

    # 소수부
    power = Decimal(1)
    for ch in frac:
        v = digval(ch)
        power *= base
        val += Decimal(v) / power

    return sign * val, [f"[{base}→10] {s} -> {sign*val}"]

def from_decimal(dec: Decimal, base: int):
    """10진 Decimal을 목표 진법 문자열로. 소수부 32자리까지 표시."""
    if base < 2 or base > 36:
        raise ValueError("기수는 2~36" )
    sign = '-' if dec < 0 else ''
    dec = abs(dec)

    # 정수부
    int_part = int(dec // 1)
    frac_part = dec - int_part
    if int_part == 0:
        int_str = '0'
    else:
        digs = []
        n = int_part
        while n > 0:
            digs.append(DIGITS[n % base])
            n //= base
        int_str = ''.join(reversed(digs))

    # 소수부 (최대 32자리)
    if frac_part == 0:
        frac_str = ''
    else:
        digs = []
        cur = frac_part
        for _ in range(32):
            cur *= base
            d = int(cur // 1)
            digs.append(DIGITS[d])
            cur -= d
            if cur == 0:
                break
        frac_str = ''.join(digs)

    return sign + (int_str if not frac_str else f"{int_str}.{frac_str}"), []

def evaluate_expression(expr: str, base: int):
    """수식을 10진 Decimal로 계산. (토큰 숫자만 {base}에서 10진으로 바꿔 eval)"""
    expr = sanitize(expr)
    if not is_valid_for_base(expr, base):
        raise ValueError(f"입력이 {base}진법에 유효하지 않음: {expr}" )

    tokens = split_tokens(expr)
    dec_tokens = []
    steps = []
    for t in tokens:
        if is_operator(t):
            dec_tokens.append(t)
        else:
            dec, _ = to_decimal(t, base)
            steps.append(f"[{base}→10] {t} -> {dec}")
            # Decimal을 문자열로 넣되 eval 호환 되도록
            dec_tokens.append(f"({str(dec)})")
    dec_expr = ''.join(dec_tokens)
    steps.append(f"[10진 수식] {dec_expr}")

    # 안전 eval: 허용 연산자만 포함된 상태 (숫자/괄호/+-*/)
    try:
        result = Decimal(str(eval(dec_expr, {"__builtins__":None}, {})))
    except Exception as e:
        raise ValueError(f"수식 계산 실패: {e}")

    steps.append(f"[10진 결과] {result}")
    return result, steps

def convert(expr: str, base_from: int, base_to: int):
    expr = sanitize(expr)
    is_expr = bool(re.search(r"[+\-*/()]", expr))
    all_steps = []
    if is_expr:
        dec, steps = evaluate_expression(expr, base_from)
        all_steps += steps
        out, _ = from_decimal(dec, base_to)
        all_steps.append(f"[10→{base_to}] {dec} -> {out}")
        return out, all_steps
    else:
        dec, steps = to_decimal(expr, base_from)
        all_steps += steps
        out, _ = from_decimal(dec, base_to)
        all_steps.append(f"[10→{base_to}] {dec} -> {out}")
        return out, all_steps
