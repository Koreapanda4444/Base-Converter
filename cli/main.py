import argparse
from converter.logic import convert, evaluate_expression, to_decimal, from_decimal

def main():
    ap = argparse.ArgumentParser(description="Base Converter CLI")
    ap.add_argument("expr", help="숫자 또는 수식 (예: 1011+1011, A.F+10)")
    ap.add_argument("--from", dest="base_from", type=int, required=True, help="입력 진법(2~36)")
    ap.add_argument("--to", dest="base_to", type=int, required=True, help="출력 진법(2~36)")
    ap.add_argument("--prec", type=int, default=12, help="소수 자릿수(표시 및 변환 정밀도, 0~32)")
    args = ap.parse_args()

    # 변환 수행 (정밀도 전달)
    out, steps = convert(args.expr, args.base_from, args.base_to, precision=args.prec)
    print(f"\n[결과]\n{out}\n")

    # 변환 과정 표시
    print("[변환 과정]")
    for s in steps:
        print("  " + s)

    # 요약 출력 (2/8/10/16)
    try:
        if any(c in args.expr for c in "+-*/()"):
            dec, _ = evaluate_expression(args.expr, args.base_from, precision=args.prec)
        else:
            dec, _ = to_decimal(args.expr, args.base_from)

        def conv(b):
            s, _ = from_decimal(dec, b, precision=args.prec)
            if "." in s and args.prec >= 0:
                ip, fp = s.split(".", 1)
                s = ip if args.prec == 0 else ip + "." + fp[:args.prec]
            return s

        print("\n[요약 결과]")
        print(f"2진수 : {conv(2)}")
        print(f"8진수 : {conv(8)}")
        print(f"10진수: {dec}")
        print(f"16진수: {conv(16)}")

    except Exception as e:
        print(f"\n요약 계산 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
