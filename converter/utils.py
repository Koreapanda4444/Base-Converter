from decimal import getcontext, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_HALF_EVEN, ROUND_CEILING, ROUND_FLOOR
import re

ROUND_MAP = {
    "반올림": ROUND_HALF_UP,
    "반내림": ROUND_HALF_DOWN,
    "짝수": ROUND_HALF_EVEN,
    "올림": ROUND_CEILING,
    "버림": ROUND_FLOOR,
}
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def set_decimal_context(precision=12, round_mode_str="HALF_UP"):
    ctx = getcontext()
    ctx.prec = max(1, int(precision))
    ctx.rounding = ROUND_MAP.get((round_mode_str or "HALF_UP").upper(), ROUND_HALF_UP)

def sanitize_expr(expr: str) -> str:
    if not expr:
        return ""
    s = expr.replace(",", ".").strip()
    s = s.replace("—", "-").replace("–", "-")
    return s

def value_of_digit(ch: str) -> int:
    u = ch.upper()
    return DIGITS.find(u)

def is_digit_for_base(ch: str, base: int) -> bool:
    v = value_of_digit(ch)
    return 0 <= v < base

_tok_re = re.compile(
    r"""
    (?P<num_mkp>\([A-Za-z0-9\.]+\)_[0-9]{1,2})|
    (?P<num_suf>[A-Za-z0-9\.]+_[0-9]{1,2})|
    (?P<num_pfx>0[bBoOxX][A-Za-z0-9\.]+)|
    (?P<num_def>[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)?)|
    (?P<id>[A-Za-z_][A-Za-z0-9_]*)|
    (?P<op>[\+\-\*\/\%\^\(\)=])
    """,
    re.VERBOSE,
)

def tokenize_mixed(expr: str):
    s = sanitize_expr(expr)
    out, i = [], 0
    while i < len(s):
        m = _tok_re.match(s, i)
        if not m:
            if s[i].isspace():
                i += 1
                continue
            raise ValueError(f"토큰화 실패: '{s[i:]}'")
        tok = m.group(0)
        i = m.end()
        out.append(tok)
    return out

def detect_number_base(tok: str, default_base: int):
    u = tok.upper()
    if u.startswith("0B"):
        return (u[2:], 2)
    if u.startswith("0O"):
        return (u[2:], 8)
    if u.startswith("0X"):
        return (u[2:], 16)
    m = re.fullmatch(r"\(([^)]+)\)_([0-9]{1,2})", u)
    if m:
        return (m.group(1), int(m.group(2)))
    m = re.fullmatch(r"([A-Z0-9\.]+)_([0-9]{1,2})", u)
    if m:
        return (m.group(1), int(m.group(2)))
    return (u, int(default_base))

def is_operator(tok: str):
    return tok in {"+", "-", "*", "/", "%", "^", "(", ")", "=", "u+", "u-"}
