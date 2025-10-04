import re
from decimal import (
    Decimal, getcontext,
    ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN
)
from .utils import DIGITS, digval, split_tokens, is_operator

# =========================================================
# ⚙️ 전역 설정
# =========================================================
DEFAULT_PRECISION = 32
DEFAULT_ROUND_MODE = ROUND_HALF_UP  # 기본 반올림 방식
ROUND_MODES = {
    "HALF_UP":   ROUND_HALF_UP,
    "HALF_DOWN": ROUND_HALF_DOWN,
    "HALF_EVEN": ROUND_HALF_EVEN,
    "CEILING":   ROUND_CEILING,
    "FLOOR":     ROUND_FLOOR,
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
        # 필요시 GUI/CLI에서 메시지 처리 가능
        pass
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
    # 정수부
    for ch in intp:
        if ch == "": 
            continue
        v = digval(ch)
        if v >= base or v < 0:
            raise ValueError(f"'{ch}'는 {base}진수에서 사용할 수 없습니다.")
        val = val * base + v

    # 소수부
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
#   - precision 길이만큼 소수부를 생성(절삭). 연산 결과의 반올림은
#     evaluate_expression()에서 Decimal.quantize로 처리.
# =========================================================
def from_decimal(dec: Decimal, base: int, precision: int = DEFAULT_PRECISION):
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
        for _ in range(max(0, precision)):
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
#   - precision + round_mode를 Decimal 컨텍스트에 반영
#   - 결과를 지정 자리수로 quantize
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

    # 소수 precision 자리까지 반올림 적용
    if precision > 0:
        quant = Decimal("1." + "0" * precision)
    else:
        quant = Decimal("1")
    result = result.quantize(quant, rounding=round_mode)

    steps.append(f"[10진 결과] {result}")
    return result, steps


# =========================================================
# 🔄 통합 변환 함수
# =========================================================
def convert(expr: str, base_from: int, base_to: int,
            precision: int = DEFAULT_PRECISION, round_mode_str: str = "HALF_UP"):
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
        # 숫자 단일 입력의 경우도 표시용 정밀/반올림을 맞추고 싶다면 아래 주석 해제
        # if precision > 0:
        #     quant = Decimal("1." + "0" * precision)
        # else:
        #     quant = Decimal("1")
        # dec = dec.quantize(quant, rounding=round_mode)

    out, _ = from_decimal(dec, base_to, precision)
    all_steps.append(f"[10→{base_to}] {dec} -> {out}")
    return out, all_steps
