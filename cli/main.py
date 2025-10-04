import argparse
from converter.logic import convert, evaluate_expression, to_decimal, from_decimal

def main():
    ap = argparse.ArgumentParser(description="Base Converter CLI")
    ap.add_argument("expr", help="숫자 또는 수식 (예: 1011+1011, A.F+10)")
    ap.add_argument("--from", dest="base_from", type=int, required=True, help="입력 진법(2~36)")
    ap.add_argument("--to", dest="base_to", type=int, required=True, help="출력 진법(2~36)")
    ap.add_argument("--prec", type=int, default=8, help="소수 자릿수(표시용, 0~32)")
    args = ap.parse_args()

    out, steps = convert(args.expr, args.base_from, args.base_to)
    print(out)

    # 요약(2/8/10/16)
    try:
        if any(c in args.expr for c in "+-*/()"):
            dec, _ = evaluate_expression(args.expr, args.base_from)
        else:
            dec, _ = to_decimal(args.expr, args.base_from)
        def conv(b):
            s, _ = from_decimal(dec, b)
            if "." in s and args.prec >= 0:
                ip, fp = s.split(".",1)
                s = ip if args.prec==0 else ip+"."+fp[:args.prec]
            return s
        print("\n[Summary]")
        print("bin:", conv(2))
        print("oct:", conv(8))
        print("dec:", str(dec))
        print("hex:", conv(16))
    except Exception:
        pass

if __name__ == "__main__":
    main()
