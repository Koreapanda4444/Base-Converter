import math
import operator
import re
from typing import List, Tuple
import ast

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGMAP = {ch: i for i, ch in enumerate(DIGITS)}

def _clean(s: str) -> str:
    return s.strip().upper()

def _valid_digit(ch: str, base: int) -> bool:
    return ch in DIGMAP and DIGMAP[ch] < base

def to_decimal(num_str: str, base: int) -> Tuple[float, List[str]]:
    """
    num_str(부호/소수점 허용)을 base에서 10진 float로.
    반환: (값, 단계 로그)
    """
    s = _clean(num_str)
    steps: List[str] = []
    if not s:
        raise ValueError("empty")

    sign = -1 if s.startswith("-") else 1
    if s and s[0] in "+-":
        s = s[1:]

    if s.count(".") > 1:
        raise ValueError("multiple dots")

    int_part, frac_part = (s.split(".", 1) + [""])[:2]

    if not int_part and not frac_part:
        raise ValueError("invalid digits")

    for ch in int_part:
        if ch and not _valid_digit(ch, base):
            raise ValueError(f"invalid digit {ch} for base {base}")
    for ch in frac_part:
        if ch and not _valid_digit(ch, base):
            raise ValueError(f"invalid digit {ch} for base {base}")

    # 정수부
    val_int = 0
    for i, ch in enumerate(int_part):
        d = DIGMAP.get(ch, 0)
        prev = val_int
        val_int = val_int * base + d
        steps.append(f"정수부: ({prev}) * {base} + {d} = {val_int}")

    # 소수부
    val_frac = 0.0
    for i, ch in enumerate(frac_part, start=1):
        d = DIGMAP.get(ch, 0)
        add = d / (base ** i)
        val_frac += add
        steps.append(f"소수부: {d} / {base}^{i} = {add:.16f}  (누적 {val_frac:.16f})")

    value = sign * (val_int + val_frac)
    steps.append(f"⇒ 10진수 = {value}")
    return value, steps

def from_decimal(value: float, base: int, precision: int = 16) -> Tuple[str, List[str]]:
    """
    10진 value를 base 표현으로. 부호/소수 포함, precision 자리까지.
    반환: (표현 문자열, 단계 로그)
    """
    steps: List[str] = []
    if math.isnan(value) or math.isinf(value):
        raise ValueError("NaN/Inf not supported")

    sign = "-" if value < 0 else ""
    v = abs(value)

    int_part = int(math.floor(v))
    frac_part = v - int_part

    # 정수부: 나눗셈/나머지
    if int_part == 0:
        int_digits = ["0"]
        steps.append("정수부: 0")
    else:
        int_digits = []
        n = int_part
        while n > 0:
            q, r = divmod(n, base)
            int_digits.append(DIGITS[r])
            steps.append(f"정수부: {n} ÷ {base} = {q} ... 나머지 {r} → '{DIGITS[r]}'")
            n = q
        int_digits.reverse()

    # 소수부: 곱셈/정수 추출
    frac_digits = []
    f = frac_part
    k = 0
    while f > 0 and k < precision:
        f *= base
        digit = int(f)
        frac_digits.append(DIGITS[digit])
        steps.append(f"소수부: ×{base} = {f:.16f} → 정수 {digit} ('{DIGITS[digit]}'), 소수 {f - digit:.16f}")
        f -= digit
        k += 1

    out = sign + "".join(int_digits)
    if frac_digits:
        out += "." + "".join(frac_digits)

    steps.append(f"⇒ {base}진수 = {out}")
    return out, steps

# -------- 수식 평가 --------

class SafeEval(ast.NodeVisitor):
    """
    +, -, *, /, 단항 +/-, 괄호만 허용.
    숫자 토큰은 선행 단계에서 10진으로 치환되어 들어온다.
    """
    def __init__(self, variables=None):
        self.vars = variables or {}

    def visit_Expression(self, node):
        return self.visit(node.body)

    # Py<3.8 호환
    def visit_Num(self, node):
        return node.n

    # Py>=3.8
    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("constants not allowed")

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op.__class__.__name__
        if op == "Add":  return operator.add(left, right)
        if op == "Sub":  return operator.sub(left, right)
        if op == "Mult": return operator.mul(left, right)
        if op == "Div":  return operator.truediv(left, right)
        raise ValueError(f"op {op} not allowed")

    def visit_UnaryOp(self, node):
        val = self.visit(node.operand)
        op = node.op.__class__.__name__
        if op == "USub": return operator.neg(val)
        if op == "UAdd": return operator.pos(val)
        raise ValueError(f"uop {op} not allowed")

    def visit_Name(self, node):
        if node.id in self.vars:
            return self.vars[node.id]
        raise ValueError("unknown name")

    def generic_visit(self, node):
        raise ValueError("unsupported expression")

def _tokenize_numbers(expr: str) -> List[Tuple[Tuple[int, int], str]]:
    """
    수식에서 숫자 토큰 위치/문자열 추출.
    숫자는 [0-9A-Z 및 .] 연속을 하나로 간주.
    """
    tokens = []
    for m in re.finditer(r"([0-9A-Za-z]+(?:\.[0-9A-Za-z]+)?)", expr):
        tokens.append(((m.start(), m.end()), m.group(0)))
    return tokens

def evaluate_expression(expr: str, base_from: int) -> Tuple[float, List[str]]:
    """
    expr을 입력 진법으로 해석(각 숫자를 base_from→10진으로 치환) 후
    10진 float로 안전하게 평가. (지원: + - * /, 단항 +/-, 괄호)
    """
    expr = expr.strip()
    steps: List[str] = []
    if not expr:
        raise ValueError("empty")

    # 숫자 토큰만 10진으로 치환
    tokens = _tokenize_numbers(expr)
    expr_dec = expr
    offset = 0
    for (a, b), tok in tokens:
        try:
            val, _ = to_decimal(tok, base_from)
            steps.append(f"[숫자] {tok} (base {base_from}) → {val}")
        except Exception:
            continue
        repl = str(val)
        expr_dec = expr_dec[:a+offset] + repl + expr_dec[b+offset:]
        offset += len(repl) - (b - a)

    steps.append(f"[치환된 수식] {expr_dec}")

    tree = ast.parse(expr_dec, mode="eval")
    val = SafeEval().visit(tree)
    steps.append(f"⇒ 10진 결과 = {val}")
    return float(val), steps

def convert(expr: str, base_from: int, base_to: int) -> Tuple[str, List[str]]:
    """
    expr가 숫자 하나든 수식이든 처리.
    - 수식: 각 숫자를 base_from→10진으로 치환→계산 → 결과를 base_to로
    - 숫자: 단순 변환
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("empty")

    if re.search(r"[+\-*/()]", expr):
        dec, s1 = evaluate_expression(expr, base_from)
        out, s2 = from_decimal(dec, base_to)
        return out, s1 + s2
    else:
        dec, s1 = to_decimal(expr, base_from)
        out, s2 = from_decimal(dec, base_to)
        return out, s1 + s2
