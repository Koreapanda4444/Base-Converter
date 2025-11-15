import argparse, csv, sys
from converter.logic import convert

GUIDE_TEXT = """
=== Base-Converter CLI Guide ===

Usage:
  python -m cli.main --from 10 --to 2 "255"
  python -m cli.main --from 2 --to 16 "1011 + 1101"

Options:
  --from, --to           2~36
  --precision            default 12
  --round                HALF_UP|HALF_DOWN|HALF_EVEN|CEILING|FLOOR
  --lower                lowercase output
  --group4               group integer part by 4
  --underscore           use '_' as group separator
  --prefix               print 0b/0o/0x
  --sci                  scientific notation (base 10)
  --sig N                significant digits
  --batch                batch mode
  --input PATH           CSV input
  --output PATH          CSV output
  --guide                show this extended help and exit

Mixed-base literals:
  0b1010, 0o77, 0xFF, (A.F)_16, 1011_2

Batch CSV example:
  expr,base_from,base_to
  0b1010+1,2,10
  (FF)_16,10,2

Examples:
  python -m cli.main --from 16 --to 2 "FF + 1"
  python -m cli.main --precision 20 --round HALF_EVEN --from 10 --to 16 "3.14159"
  python -m cli.main --batch --input in.csv --output out.csv
"""

def _do_convert(expr, args):
    """Helper function to avoid code duplication."""
    return convert(
        expr,
        args.base_from,
        args.base_to,
        precision=args.precision,
        round_mode_str=args.round,
        fmt={
            "letter_case": "lower" if args.lower else "upper",
            "group_size": 4 if args.group4 else 0,
            "group_sep": "_" if args.underscore else " ",
            "prefix": args.prefix,
            "sci": args.sci,
            "sig": args.sig or 0,
        }
    )

def run_once(args):
    out, _ = _do_convert(args.expr, args)
    print(out)

def run_batch(args):
    rows = []
    fieldnames = []
    try:
        with open(args.input, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            if "result" not in fieldnames:
                fieldnames.append("result")

            for i, row in enumerate(reader, 1):
                try:
                    # Allow falling back to command-line bases
                    original_bfrom, original_bto = args.base_from, args.base_to
                    args.base_from = int(row.get("base_from") or original_bfrom)
                    args.base_to = int(row.get("base_to") or original_bto)
                    
                    expr = row.get("expr") or row.get("input") or ""
                    out, _ = _do_convert(expr, args)
                    row["result"] = out
                    
                    # Restore original bases for next iteration
                    args.base_from, args.base_to = original_bfrom, original_bto
                except Exception as e:
                    print(f"Warning: Row {i} 처리 실패 - {e}", file=sys.stderr)
                    row["result"] = f"ERROR: {e}"
                rows.append(row)
    except FileNotFoundError:
        print(f"Error: 입력 파일 '{args.input}'을 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("Warning: 입력 파일이 비어있거나 읽을 데이터가 없습니다.")
        return

    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"성공적으로 {args.output}에 저장했습니다.")

def main():
    p = argparse.ArgumentParser(add_help=False, description="Base Converter CLI")
    p.add_argument("--from", dest="base_from", type=int, default=10)
    p.add_argument("--to", dest="base_to", type=int, default=2)
    p.add_argument("--precision", type=int, default=12)
    p.add_argument("--round", dest="round", type=str, default="HALF_UP")
    p.add_argument("--lower", action="store_true")
    p.add_argument("--group4", action="store_true")
    p.add_argument("--underscore", action="store_true")
    p.add_argument("--prefix", action="store_true")
    p.add_argument("--sci", action="store_true")
    p.add_argument("--sig", type=int, default=0)
    p.add_argument("--batch", action="store_true")
    p.add_argument("--input", type=str, default="")
    p.add_argument("--output", type=str, default="out.csv")
    p.add_argument("--guide", action="store_true")
    p.add_argument("expr", nargs="?", default="")
    args = p.parse_args()

    if args.guide:
        print(GUIDE_TEXT.strip())
        sys.exit(0)

    try:
        if args.batch:
            if not args.input:
                print("Error: 배치 모드에서는 --input 인자가 필수입니다.", file=sys.stderr)
                sys.exit(1)
            run_batch(args)
        else:
            if not args.expr:
                print("Error: 변환할 식이 필요합니다. (예: 'FF' 또는 '10+20')", file=sys.stderr)
                sys.exit(1)
            run_once(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()