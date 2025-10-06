from __future__ import annotations
from decimal import Decimal
from fractions import Fraction
from typing import List, Tuple, Optional, Dict
from converter.utils import (
    set_decimal_context, sanitize_expr, tokenize_mixed, detect_number_base,
    is_operator, is_digit_for_base, value_of_digit, DIGITS
)
from converter import vars as V

def _int_to_base_str(n: int, base: int) -> str:
    if n == 0: return "0"
    s = []
    x = n
    while x > 0:
        s.append(DIGITS[x % base])
        x //= base
    return "".join(reversed(s))

def _apply_letter_case(s: str, letter_case: str) -> str:
    return s.lower() if (letter_case or "").lower() == "lower" else s

def _apply_grouping(int_part: str, group_size: int, group_sep: str) -> str:
    if group_size <= 0: return int_part
    rev = int_part[::-1]
    chunks = [rev[i:i+group_size] for i in range(0, len(rev), group_size)]
    return (group_sep.join(chunks))[::-1]

def _prefix_for_base(base: int, letter_case: str) -> str:
    m = {2: "0b", 8: "0o", 16: "0x"}
    p = m.get(base, "")
    return p if (letter_case or "").lower() == "lower" else p.upper()

def _fraction_to_base(fr: Fraction, base: int, precision: int = 12, fmt: Optional[Dict] = None) -> Tuple[str, List[str]]:
    steps: List[str] = []
    fmt = fmt or {}
    letter_case = fmt.get("letter_case", "upper")
    group_size = int(fmt.get("group_size", 0) or 0)
    group_sep = str(fmt.get("group_sep", " "))
    use_prefix = bool(fmt.get("prefix", False))
    use_sci = bool(fmt.get("sci", False))
    sig = int(fmt.get("sig", 0) or 0)
    if fr == 0:
        out = "0"
        return out, steps
    sign = "-" if fr < 0 else ""
    fr = -fr if fr < 0 else fr
    ip = fr.numerator // fr.denominator
    rp = fr.numerator % fr.denominator
    int_part_raw = _int_to_base_str(ip, base)
    if rp == 0:
        int_fmt = _apply_grouping(int_part_raw, group_size, group_sep)
        int_fmt = _apply_letter_case(int_fmt, letter_case)
        pref = _prefix_for_base(base, letter_case) if use_prefix else ""
        result = f"{sign}{pref}{int_fmt}"
        return result, steps
    digits: List[str] = []
    seen = {}
    cycle_start = None
    rem = rp
    den = fr.denominator
    while rem != 0:
        if rem in seen:
            cycle_start = seen[rem]
            break
        seen[rem] = len(digits)
        rem *= base
        digit = rem // den
        rem = rem % den
        digits.append(DIGITS[int(digit)])
        if cycle_start is None and len(digits) >= max(precision, 1) and rem not in seen:
            break
    int_fmt = _apply_grouping(int_part_raw, group_size, group_sep)
    if cycle_start is not None:
        nonrep = "".join(digits[:cycle_start])
        rep = "".join(digits[cycle_start:])
        frac_part = f"{nonrep}({rep})"
    else:
        frac_part = "".join(digits)
    if sig > 0 and "(" not in frac_part:
        mant = int_part_raw + frac_part
        if len(mant) > sig:
            cut = max(0, sig - len(int_part_raw))
            frac_part = frac_part[:cut]
    int_fmt = _apply_letter_case(int_fmt, letter_case)
    frac_fmt = _apply_letter_case(frac_part, letter_case)
    pref = _prefix_for_base(base, letter_case) if use_prefix else ""
    out = f"{sign}{pref}{int_fmt}.{frac_fmt}"
    if use_sci and base == 10 and sig > 0 and "(" not in frac_fmt:
        raw = (int_part_raw + "." + frac_part).lstrip("0")
        if raw.startswith("."):
            k = 0
            for c in frac_part:
                if c == "0": k += 1
                else: break
            if len(frac_part) > k:
                mant = frac_part[k] + (("." + frac_part[k+1:]) if len(frac_part[k+1:])>0 else "")
                exp = -(k+1)
            else:
                mant, exp = "0", 0
        else:
            mant = int_part_raw[0] + (("." + int_part_raw[1:] + frac_part) if (len(int_part_raw)>1 or len(frac_part)>0) else "")
            exp = len(int_part_raw) - 1
        mtrim = mant.replace(".","")
        if len(mtrim) > sig:
            need = sig + (1 if "." in mant else 0)
            mant = mant[:need]
        out = f"{sign}{mant}e{('+' if exp>=0 else '')}{exp}"
    return out, steps

def to_decimal(num_str: str, base_from: int):
    s = sanitize_expr(num_str).upper()
    if "." in s:
        a, b = s.split(".", 1)
    else:
        a, b = s, ""
    if a == "" and b == "": raise ValueError("빈 숫자입니다.")
    if a and any(not is_digit_for_base(ch, base_from) for ch in a): raise ValueError(f"{base_from}진수 자리수 오류: {s}")
    if b and any(not is_digit_for_base(ch, base_from) for ch in b): raise ValueError(f"{base_from}진수 자리수 오류: {s}")
    val = Decimal(0)
    for i, ch in enumerate(a[::-1]): val += value_of_digit(ch) * (base_from ** i)
    for i, ch in enumerate(b, start=1): val += Decimal(value_of_digit(ch)) / (base_from ** i)
    return val, [f"[to_decimal] {s} ({base_from}) → {val}"]

def from_decimal(dec_val, base_to: int, precision=12, fmt: Optional[Dict]=None):
    steps: List[str] = []
    if isinstance(dec_val, Fraction):
        fr = dec_val
    else:
        try:
            fr = Fraction(str(dec_val))
        except Exception:
            fr = Fraction(float(dec_val))
    out, st2 = _fraction_to_base(fr, base_to, precision=precision, fmt=fmt)
    steps.extend(st2)
    return out, steps

def _token_to_fraction_default(tok: str, base_from: int) -> Fraction:
    if "." in tok:
        ip, fp = tok.split(".", 1)
    else:
        ip, fp = tok, ""
    v = 0
    for ch in ip:
        if ch and not is_digit_for_base(ch, base_from): raise ValueError(f"{base_from}진수 자리수 오류: {tok}")
        v = v * base_from + (value_of_digit(ch) if ch else 0)
    fr = Fraction(v, 1)
    den = 1
    for ch in fp:
        if not is_digit_for_base(ch, base_from): raise ValueError(f"{base_from}진수 자리수 오류: {tok}")
        den *= base_from
        fr += Fraction(value_of_digit(ch), den)
    return fr

def _token_to_fraction_mixed(tok: str, default_base: int) -> Fraction:
    raw, base = detect_number_base(tok, default_base)
    return _token_to_fraction_default(raw, base)

def _apply_unary_frac(op: str, a: Fraction) -> Fraction:
    return a if op == "u+" else -a

def _apply_binary_frac(op: str, a: Fraction, b: Fraction) -> Fraction:
    if op == "+": return a + b
    if op == "-": return a - b
    if op == "*": return a * b
    if op == "/":
        if b == 0: raise ZeroDivisionError("0으로 나눌 수 없습니다.")
        return a / b
    if op == "%":
        if b == 0: raise ZeroDivisionError("0으로 나눌 수 없습니다.")
        q = a // b
        return a - q * b
    if op == "^":
        if b.denominator != 1: raise ValueError("분수 지수는 지원하지 않습니다.")
        n = b.numerator
        if n >= 0: return a ** n
        if a == 0: raise ZeroDivisionError("0의 음수 거듭제곱 불가")
        return Fraction(1, 1) / (a ** (-n))
    raise ValueError(f"알 수 없는 연산자: {op}")

def _shunting_yard(tokens):
    prec = {"u+":4,"u-":4,"^":3,"*":2,"/":2,"%":2,"+":1,"-":1}
    right_assoc = {"^"}
    out, op = [], []
    def is_unary(prev): return (prev is None) or (prev in {"+","-","*","/","%","^","(","u+","u-","="})
    prev = None
    for t in tokens:
        if t == "(":
            op.append(t); prev = t; continue
        if t == ")":
            while op and op[-1] != "(": out.append(op.pop())
            if not op: raise ValueError("괄호 오류")
            op.pop(); prev = t; continue
        if t in {"+","-"}:
            if is_unary(prev):
                ut = "u+" if t=="+" else "u-"
                while op and op[-1]!="(" and prec.get(op[-1],-1) > prec[ut]: out.append(op.pop())
                op.append(ut)
            else:
                while op and op[-1]!="(":
                    top = op[-1]
                    if (top in right_assoc and prec[top] > prec[t]) or (top not in right_assoc and prec[top] >= prec[t]):
                        out.append(op.pop())
                    else: break
                op.append(t)
            prev = t; continue
        if t in {"*","/","%","^"}:
            while op and op[-1]!="(":
                top = op[-1]
                if top in right_assoc:
                    if prec[top] > prec[t]: out.append(op.pop())
                    else: break
                else:
                    if prec[top] >= prec[t]: out.append(op.pop())
                    else: break
            op.append(t); prev = t; continue
        if t == "=":
            out.append(t); prev = t; continue
        out.append(t); prev = "VAL"
    while op:
        top = op.pop()
        if top in {"(", ")"}: raise ValueError("괄호 오류")
        out.append(top)
    return out

def evaluate_expression(expr: str, base_from: int, precision=12, round_mode="HALF_UP"):
    set_decimal_context(precision, round_mode)
    s = sanitize_expr(expr)
    tokens = tokenize_mixed(s)
    if "=" in tokens:
        if tokens.count("=") != 1: raise ValueError("할당식은 한 번만 사용할 수 있습니다.")
        eq_i = tokens.index("=")
        if eq_i == 0: raise ValueError("좌변이 없습니다.")
        name = tokens[0]
        if not name or not name[0].isalpha() and name[0] != "_": raise ValueError("유효한 변수명이 아닙니다.")
        rhs = tokens[eq_i+1:]
        if not rhs: raise ValueError("우변이 없습니다.")
        val, _ = _eval_rpn(_shunting_yard(rhs), base_from)
        V.set_var(name, val)
        return val, [f"[assign] {name} = {val.numerator}/{val.denominator}"]
    rpn = _shunting_yard(tokens)
    val, steps = _eval_rpn(rpn, base_from)
    return val, steps

def _eval_rpn(rpn, default_base: int):
    stack: List[Fraction] = []
    for t in rpn:
        if t in {"u+","u-","+","-","*","/","%","^","="}:
            if t in {"u+","u-"}:
                if not stack: raise ValueError("단항 오류")
                a = stack.pop()
                stack.append(_apply_unary_frac(t, a))
            elif t == "=":
                raise ValueError("잘못된 위치의 '='")
            else:
                if len(stack) < 2: raise ValueError("피연산자 부족")
                b = stack.pop(); a = stack.pop()
                stack.append(_apply_binary_frac(t, a, b))
        else:
            if t[0].isalpha() and (t not in {"INF","NAN"}) and not any(ch in t for ch in "._0123456789"):
                stack.append(V.resolve(t))
            else:
                stack.append(_token_to_fraction_mixed(t, default_base))
    if len(stack) != 1: raise ValueError("수식 오류")
    return stack[0], [f"[rpn] ok"]

def convert(expr: str, base_from: int, base_to: int, precision=12, round_mode_str="HALF_UP", fmt: Optional[Dict]=None):
    set_decimal_context(precision, round_mode_str)
    s = sanitize_expr(expr)
    if any(op in s for op in "+-*/()%^="):
        fr, steps1 = evaluate_expression(s, base_from, precision, round_mode_str)
        out, steps2 = from_decimal(fr, base_to, precision, fmt=fmt)
        return out, steps1 + steps2
    else:
        fr = _token_to_fraction_mixed(s, base_from)
        out, steps2 = from_decimal(fr, base_to, precision, fmt=fmt)
        return out, [f"[to_fraction] {s}"] + steps2
