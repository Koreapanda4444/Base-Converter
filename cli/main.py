# cli/main.py
import argparse, csv, sys
from converter.logic import convert

GUIDE_TEXT = """
=== Base-Converter CLI Guide ===

Usage:
  python cli/main.py --from 10 --to 2 "255"
  python cli/main.py --from 2 --to 16 "1011 + 1101"

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
  python cli/main.py --from 16 --to 2 "FF + 1"
  python cli/main.py --precision 20 --round HALF_EVEN --from 10 --to 16 "3.14159"
  python cli/main.py --batch --input in.csv --output out.csv
"""

def run_once(args):
    out, _ = convert(args.expr, args.base_from, args.base_to, precision=args.precision, round_mode_str=args.round, fmt={
        "letter_case": "lower" if args.lower else "upper",
        "group_size": 4 if args.group4 else 0,
        "group_sep": "_" if args.underscore else " ",
        "prefix": args.prefix,
        "sci": args.sci,
        "sig": args.sig or 0,
    })
    print(out)

def run_batch(args):
    rows = []
    with open(args.input, "r", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            expr = row.get("expr") or row.get("input") or ""
            bfrom = int(row.get("base_from") or args.base_from)
            bto = int(row.get("base_to") or args.base_to)
            out, _ = convert(expr, bfrom, bto, precision=args.precision, round_mode_str=args.round, fmt={
                "letter_case": "lower" if args.lower else "upper",
                "group_size": 4 if args.group4 else 0,
                "group_sep": "_" if args.underscore else " ",
                "prefix": args.prefix,
                "sci": args.sci,
                "sig": args.sig or 0,
            })
            row["result"] = out
            rows.append(row)
    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def main():
    p = argparse.ArgumentParser(add_help=True)
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

    if args.batch:
        if not args.input:
            print("input CSV 필요 (--input path)", file=sys.stderr); sys.exit(1)
        run_batch(args)
    else:
        if not args.expr:
            print("식이 필요합니다", file=sys.stderr); sys.exit(1)
        run_once(args)

if __name__ == "__main__":
    main()
