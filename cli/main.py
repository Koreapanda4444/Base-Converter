# cli/main.py
import argparse
from converter.logic import convert

def main():
    parser = argparse.ArgumentParser(description="Base Converter CLI")
    parser.add_argument("--from", dest="base_from", type=int, required=True)
    parser.add_argument("--to", dest="base_to", type=int, required=True)
    parser.add_argument("expr", help="변환할 숫자 또는 식")
    args = parser.parse_args()

    result, steps = convert(args.expr, args.base_from, args.base_to)
    print(f"결과: {result}")
    print("\n변환 과정:")
    for s in steps:
        print(" ", s)

if __name__ == "__main__":
    main()
