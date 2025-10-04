# converter/utils.py
from decimal import Decimal, getcontext, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_HALF_EVEN, ROUND_CEILING, ROUND_FLOOR

ROUND_MAP = {
    "HALF_UP": ROUND_HALF_UP,
    "HALF_DOWN": ROUND_HALF_DOWN,
    "HALF_EVEN": ROUND_HALF_EVEN,
    "CEILING": ROUND_CEILING,
    "FLOOR": ROUND_FLOOR,
}

def set_decimal_context(precision=12, round_mode_str="HALF_UP"):
    ctx = getcontext()
    ctx.prec = max(1, precision)
    ctx.rounding = ROUND_MAP.get(round_mode_str.upper(), ROUND_HALF_UP)

def sanitize_expr(expr: str) -> str:
    return expr.replace(" ", "").replace(",", ".").upper()
