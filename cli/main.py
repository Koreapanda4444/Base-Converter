import argparse, csv, sys
from converter.logic import convert

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
    p = argparse.ArgumentParser()
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
    p.add_argument("expr", nargs="?", default="")
    args = p.parse_args()
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
