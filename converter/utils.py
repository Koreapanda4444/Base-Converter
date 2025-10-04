import re

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_op_re = re.compile(r'([+\-*/()])')

def sanitize(s: str) -> str:
    if not s: return ""
    s = s.replace(" ", "").replace("_", "").replace(",", "")
    # 대문자화
    return s.upper()

def split_tokens(expr: str):
    if not expr: return []
    parts = [p for p in _op_re.split(expr) if p != ""]
    return parts

def is_operator(tok: str) -> bool:
    return tok in {"+","-","*","/","(",")"}

def digval(ch: str) -> int:
    ch = ch.upper()
    return DIGITS.find(ch)

def is_valid_token_number(tok: str, base: int) -> bool:
    # 허용: 숫자(0-9A-Z)와 '.' 한 번
    if tok.count(".") > 1: return False
    for ch in tok:
        if ch == ".": continue
        v = digval(ch)
        if v < 0 or v >= base:
            return False
    return True

def is_valid_for_base(expr: str, base: int) -> bool:
    for t in split_tokens(expr):
        if is_operator(t): continue
        if not is_valid_token_number(t, base):
            return False
    return True
