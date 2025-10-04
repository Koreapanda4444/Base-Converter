import re
from decimal import Decimal, getcontext
from .utils import DIGITS, digval, split_tokens, is_operator

# =========================================================
# ⚙️ 전역 정밀도 설정 (기본 32, CLI/GUI에서 변경 가능)
# =========================================================
DEFAULT_PRECISION = 32
getcontext().prec = DEFAULT_PRECISION


# =========================================================
# 🔧 입력 자동 보정 (공백, 소문자, 불필요한 문자 제거)
# =========================================================
def normalize_input(value: str, base: int) -> str:
    """
    입력 문자열을 정리 및 진법 범위 내 문자만 남김.
    - 공백, 밑줄, 쉼표 제거
    - 소문자 → 대문자
    - 진법 범위 초과 문자 제거
    """
    if not value:
        return ""
    value = value.strip().replace(" ", "").replace("_", "").replace(",", "").upper()

    valid_chars = DIGITS[:base] + ".-+*/()"
    filtered = "".join(ch for ch in value if ch in valid_chars)
    if filtered != value:
        print("[경고] 일부 문자가 진법 범위를 벗어나 제거되었습니다.")
    return filtered


# =========================================================
# 🧮 진법 → 10진 변환
# =========================================================
def to_decimal(s: str, base: int):
    """문자열 s(부호/소수점 포함)를 10진 Decimal로 변환."""
    s = normalize_input(s, base)

    # 음수 처리
    sign = 1
    if s.startswith('-'):
        sign = -1
        s = s[1:]
    if '.' in s:
        intp, frac = s.split('.', 1)
    else:
        intp, frac = s, ""

    val = Decimal(0)
    # 정수부 변환
    for ch in intp:
        if ch == "": 
            continue
        v = digval(ch)
        if v >= base or v < 0:
            raise ValueError(f"'{ch}'는 {base}진수에서 사용할 수 없습니다.")
        val = val * base + v

    # 소수부 변환
    power = Decimal(1)
    for ch in frac:
        v = digval(ch)
        if v >= base or v < 0:
            raise ValueError(f"'{ch}'는 {base}진수에서 사용할 수 없습니다.")
        power *= base
        val += Decimal(v) / power

    result = sign * val
    steps = [f"[{base}→10] {s} -> {result}"]
    return result, steps


# =========================================================
# 🔁 10진 → 목표 진법 변환
# =========================================================
def from_decimal(dec: Decimal, base: int, precision: int = DEFAULT_PRECISION):
    """10진 Decimal을 목표 진법 문자열로. 소수부 precision 자리까지 표시."""
    if base < 2 or base > 36:
        raise ValueError("기수는 2~36 사이여야 합니다.")

    sign = '-' if dec < 0 else ''
    dec = abs(dec)

    int_part = int(dec // 1)
    frac_part = dec - int_part

    # 정수부
    if int_part == 0:
        int_str = '0'
    else:
        digs = []
        n = int_part
        while n > 0:
            digs.append(DIGITS[n % base])
            n //= base
        int_str = ''.join(reversed(digs))

    # 소수부
    if frac_part == 0:
        frac_str = ''
    else:
        digs = []
        cur = frac_part
        for _ in range(precision):
            cur *= base
            d = int(cur // 1)
            digs.append(DIGITS[d])
            cur -= d
            if cur == 0:
                break
        frac_str = ''.join(digs)

    return sign + (int_str if not frac_str else f"{int_str}.{frac_str}"), []


# =========================================================
# 🧩 진법 수식 계산기 (eval 안전 제한)
# =========================================================
def evaluate_expression(expr: str, base: int, precision: int = DEFAULT_PRECISION):
    """진법 수식을 10진 Decimal로 계산."""
    expr = normalize_input(expr, base)
    tokens = split_tokens(expr)
    dec_tokens = []
    steps = []

    for t in tokens:
        if is_operator(t):
            dec_tokens.append(t)
        else:
            dec, _ = to_decimal(t, base)
            steps.append(f"[{base}→10] {t} -> {dec}")
            dec_tokens.append(f"({str(dec)})")

    dec_expr = ''.join(dec_tokens)
    steps.append(f"[10진 수식] {dec_expr}")

    # 안전한 eval 실행
    try:
        result = Decimal(str(eval(dec_expr, {"__builtins__": None}, {})))
    except Exception as e:
        raise ValueError(f"수식 계산 실패: {e}")

    getcontext().prec = precision
    steps.append(f"[10진 결과] {result}")
    return result, steps


# =========================================================
# 🔄 통합 변환 함수 (진법 ↔ 진법)
# =========================================================
def convert(expr: str, base_from: int, base_to: int, precision: int = DEFAULT_PRECISION):
    """
    expr: 변환할 표현식 (숫자 or 수식)
    base_from: 입력 진법
    base_to: 출력 진법
    precision: 소수부 정밀도 (기본 32)
    """
    expr = normalize_input(expr, base_from)
    is_expr = bool(re.search(r"[+\-*/()]", expr))
    all_steps = []

    if is_expr:
        dec, steps = evaluate_expression(expr, base_from, precision)
        all_steps += steps
    else:
        dec, steps = to_decimal(expr, base_from)
        all_steps += steps

    out, _ = from_decimal(dec, base_to, precision)
    all_steps.append(f"[10→{base_to}] {dec} -> {out}")
    return out, all_steps
