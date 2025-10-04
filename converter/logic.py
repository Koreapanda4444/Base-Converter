import re
from decimal import Decimal, getcontext, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN
from .utils import DIGITS, digval, split_tokens, is_operator

# =========================================================
# ⚙️ 전역 설정
# =========================================================
DEFAULT_PRECISION = 32
DEFAULT_ROUND_MODE = ROUND_HALF_UP  # 기본 반올림 방식
ROUND_MODES = {
    "HALF_UP": ROUND_HALF_UP,
    "HALF_DOWN": ROUND_HALF_DOWN,
    "HALF_EVEN": ROUND_HALF_EVEN,
    "CEILING": ROUND_CEILING,
    "FLOOR": ROUND_FLOOR,
}

getcontext().prec = DEFAULT_PRECISION
getcontext().rounding = DEFAULT_ROUND_MODE


# =========================================================
# 🔧 입력 보정
# =========================================================
def normalize_input(value: str, base: int) -> str:
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
    s = normalize_input(s, base)
    sign = 1
    if s.startswith('-'):
        sign = -1
        s = s[1:]
    if '.' in s:
        intp, frac = s.split('.', 1)
    else:
        intp, frac = s, ""

    val = Decimal(0)
    for ch in intp:
        if ch == "": continue
        v = digval(ch)
        if v >= base or v < 0:
            raise ValueError(f"'{ch}'는 {base}진수에서 사용할 수 없습니다.")
        val = val * base + v

    power = Decimal(1)
    for ch in frac:
        v = digval(ch)
        if v >= base or v < 0:
            raise ValueError(f"'{ch}'는 {base}진수에서 사용할 수 없습니다.")
        power *= base
        val += Decimal(v) / power

    result = sign * val
    return result, [f"[{base}→10] {s} -> {result}"]


# =========================================================
# 🔁 10진 → 목표 진법 변환
# =========================================================
def from_decimal(dec: Decimal, base: int, precision: int = DEFAULT_PRECISION):
    if base < 2 or base > 36:
        raise ValueError("기수는 2~36 사이여야 합니다.")

    sign = '-' if dec < 0 else ''
    dec = abs(dec)

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
# 🧩 진법 수식 계산기
# =========================================================
def evaluate_expression(expr: str, base: int, precision: int = DEFAULT_PRECISION, round_mode=DEFAULT_ROUND_MODE):
    expr = normalize_input(expr, base)
    getcontext().prec = precision
    getcontext().rounding = round_mode

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

    try:
        result = Decimal(str(eval(dec_expr, {"__builtins__": None}, {})))
    except Exception as e:
        raise ValueError(f"수식 계산 실패: {e}")

    result = result.quantize(Decimal("1." + "0" * precision), rounding=round_mode)
    steps.append(f"[10진 결과] {result}")
    return result, steps


# =========================================================
# 🔄 통합 변환 함수
# =========================================================
def convert(expr: str, base_from: int, base_to: int, precision: int = DEFAULT_PRECISION, round_mode_str: str = "HALF_UP"):
    expr = normalize_input(expr, base_from)
    round_mode = ROUND_MODES.get(round_mode_str.upper(), DEFAULT_ROUND_MODE)
    getcontext().prec = precision
    getcontext().rounding = round_mode

    is_expr = bool(re.search(r"[+\-*/()]", expr))
    all_steps = []

    if is_expr:
        dec, steps = evaluate_expression(expr, base_from, precision, round_mode)
        all_steps += steps
    else:
        dec, steps = to_decimal(expr, base_from)
        all_steps += steps

    out, _ = from_decimal(dec, base_to, precision)
    all_steps.append(f"[10→{base_to}] {dec} -> {out}")
    return out, all_steps
