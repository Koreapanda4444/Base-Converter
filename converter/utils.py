# converter/utils.py
from decimal import getcontext, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_HALF_EVEN, ROUND_CEILING, ROUND_FLOOR
import re

ROUND_MAP = {
    "HALF_UP": ROUND_HALF_UP,
    "HALF_DOWN": ROUND_HALF_DOWN,
    "HALF_EVEN": ROUND_HALF_EVEN,
    "CEILING": ROUND_CEILING,
    "FLOOR": ROUND_FLOOR,
}

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def set_decimal_context(precision=12, round_mode_str="HALF_UP"):
    ctx = getcontext()
    ctx.prec = max(1, precision)
    ctx.rounding = ROUND_MAP.get(round_mode_str.upper(), ROUND_HALF_UP)

def sanitize_expr(expr: str) -> str:
    # 공백 제거, 소수점은 '.' 고정, 대문자 통일
    return expr.replace(" ", "").replace(",", ".").upper()

def value_of_digit(ch: str) -> int:
    if ch not in DIGITS:
        return -1
    return DIGITS.index(ch)

def is_digit_for_base(ch: str, base: int) -> bool:
    v = value_of_digit(ch)
    return 0 <= v < base

def tokenize(expr: str, base_from: int):
    """
    입력 진법 기준으로 숫자/연산자/괄호를 토큰화.
    단항부호 처리는 셔닝야드 단계에서 한다.
    """
    tokens = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]

        # 숫자(해당 진법 허용) 또는 소수점
        if ch == '.' or is_digit_for_base(ch, base_from):
            j = i
            dot_seen = (ch == '.')
            j += 1
            while j < n:
                c = expr[j]
                if c == '.':
                    if dot_seen:
                        break
                    dot_seen = True
                    j += 1
                    continue
                if not is_digit_for_base(c, base_from):
                    break
                j += 1
            tokens.append(expr[i:j])  # ex) "1A.F"
            i = j
            continue

        # 연산자/괄호
        if ch in "+-*/%^()":
            tokens.append(ch)
            i += 1
            continue

        # 알 수 없는 문자
        raise ValueError(f"잘못된 문자: '{ch}'")
    return tokens

def shunting_yard(tokens):
    """
    토큰 시퀀스를 RPN으로 변환.
    단항 +/− 는 u+ / u- 로 표기하여 구분.
    ^ 은 오른쪽 결합. 그 외는 왼쪽 결합.
    """
    # 우선순위 (높을수록 우선)
    prec = {
        "u+": 4, "u-": 4,
        "^": 3,
        "*": 2, "/": 2, "%": 2,
        "+": 1, "-": 1,
    }
    right_assoc = {"^"}  # 오른쪽 결합

    out = []
    op = []

    # 단항 판정: 이전 토큰이 비었거나, 직전이 연산자/왼괄호면 단항 가능
    def is_unary_position(prev):
        return (prev is None) or (prev in {"+", "-", "*", "/", "%", "^", "(", "u+", "u-"})
    prev = None

    for t in tokens:
        if t == "(":
            op.append(t)
            prev = "("
        elif t == ")":
            while op and op[-1] != "(":
                out.append(op.pop())
            if not op or op[-1] != "(":
                raise ValueError("괄호가 올바르지 않습니다.")
            op.pop()  # pop '('
            prev = ")"
        elif t in {"+", "-"}:
            # 단항 변환
            if is_unary_position(prev):
                ut = "u+" if t == "+" else "u-"
                while op and op[-1] != "(" and prec.get(op[-1], -1) > prec[ut]:
                    out.append(op.pop())
                op.append(ut)
            else:
                # 이항 +/-
                while op and op[-1] != "(":
                    top = op[-1]
                    if (top in prec and
                        ((top in right_assoc and prec[top] > prec[t]) or
                         (top not in right_assoc and prec[top] >= prec[t]))):
                        out.append(op.pop())
                    else:
                        break
                op.append(t)
            prev = t
        elif t in {"*", "/", "%", "^"}:
            while op and op[-1] != "(":
                top = op[-1]
                if top in prec:
                    if top in right_assoc:
                        if prec[top] > prec[t]:
                            out.append(op.pop())
                        else:
                            break
                    else:
                        if prec[top] >= prec[t]:
                            out.append(op.pop())
                        else:
                            break
                else:
                    break
            op.append(t)
            prev = t
        else:
            # 숫자 토큰
            out.append(t)
            prev = "NUM"

    while op:
        top = op.pop()
        if top == "(" or top == ")":
            raise ValueError("괄호가 올바르지 않습니다.")
        out.append(top)
    return out
