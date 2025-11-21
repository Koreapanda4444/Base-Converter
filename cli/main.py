import argparse, csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from converter.logic import convert
except ModuleNotFoundError:
    print(f"오류: 'converter' 패키지를 찾을 수 없습니다. 루트 경로 추가됨: {ROOT}", file=sys.stderr)
    print("대안 실행:\n  cd d:\\vscode_script\\python\\Base-Converter\n  python -m cli.main --from 10 --to 2 255", file=sys.stderr)
    raise

GUIDE_TEXT = """
=== Base-Converter CLI 가이드 ===

사용법:
  python -m cli.main --from 10 --to 2 "255"
  python -m cli.main --from 2 --to 16 "1011 + 1101"

옵션:
  --from, --to           변환할 진법 (2~36).
  --precision            소수점 이하 정밀도 (기본값: 12).
  --round                반올림 모드: HALF_UP, HALF_DOWN, HALF_EVEN, CEILING, FLOOR.
  --lower                결과를 소문자로 출력합니다 (a-z).
  --group4               정수부를 4자리씩 묶어서 표시합니다.
  --underscore           자릿수 구분자로 공백 대신 '_'를 사용합니다.
  --prefix               결과에 진법 접두사를 추가합니다 (0b, 0o, 0x).
  --sci                  10진수 결과에 과학적 표기법을 사용합니다.
  --sig N                결과를 N개의 유효숫자로 포맷합니다.
  --batch                CSV 파일을 이용한 일괄 변환 모드를 활성화합니다.
  --input PATH           일괄 변환에 사용할 입력 CSV 파일 경로.
  --output PATH          결과를 저장할 CSV 파일 경로 (기본값: out.csv).
  --guide                이 확장된 도움말 메시지를 보고 종료합니다.

표현식 내 혼합 진법:
  표현식 안에서 0b, 0o, 0x 같은 접두사를 사용하여 다른 진법의 숫자를 바로 사용할 수 있습니다.
  예시: "0xFF + 1" 은 255 + 1 로 계산됩니다.

일괄 변환 CSV 파일 형식:
  CSV 파일은 헤더를 포함해야 합니다. 'expr'(또는 'input'), 'base_from', 'base_to' 컬럼을 사용합니다.
  
  예시 (input.csv):
  expr,base_from,base_to
  0b1010+1,2,10
  (FF)_16,10,2
"""

def _get_format_options(args):
    """인자로부터 포맷 옵션 딕셔너리를 생성합니다."""
    return {
        "letter_case": "lower" if args.lower else "upper",
        "group_size": 4 if args.group4 else 0,
        "group_sep": "_" if args.underscore else " ",
        "prefix": args.prefix,
        "sci": args.sci,
        "sig": args.sig or 0,
    }

def run_once(args):
    """단일 표현식을 변환하고 결과를 출력합니다."""
    fmt = _get_format_options(args)
    out, _ = convert(args.expr, args.base_from, args.base_to, args.precision, args.round, fmt)
    print(out)

def run_batch(args):
    """CSV 파일을 읽어 일괄 변환을 수행하고 결과를 저장합니다."""
    rows = []
    fieldnames = []
    fmt = _get_format_options(args)

    try:
        with open(args.input, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            if "result" not in fieldnames:
                fieldnames.append("result")

            for i, row in enumerate(reader, 1):
                try:
                    b_from = int(row.get("base_from") or args.base_from)
                    b_to = int(row.get("base_to") or args.base_to)
                    expr = row.get("expr") or row.get("input") or ""
                    
                    out, _ = convert(expr, b_from, b_to, args.precision, args.round, fmt)
                    row["result"] = out
                except Exception as e:
                    print(f"경고: {i}번째 행 처리 실패 - {e}", file=sys.stderr)
                    row["result"] = f"오류: {e}"
                rows.append(row)
    except FileNotFoundError:
        print(f"오류: 입력 파일을 찾을 수 없습니다: '{args.input}'", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("경고: 입력 파일이 비어있거나 읽을 데이터가 없습니다.")
        return

    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"성공적으로 처리하여 '{args.output}'에 저장했습니다.")

def repl(args):
    """대화형 모드: 표현식을 반복 입력받아 변환."""
    print("Interactive mode 시작. (종료: :q 또는 :quit)")
    print("명령: :set from N | :set to N | :help")
    while True:
        try:
            line = input(f"[from={args.base_from} -> to={args.base_to}] expr> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        low = line.lower()
        if low in (":q", ":quit", ":exit", "q", "quit", "exit"):
            break
        if low in (":h", ":help", "help"):
            print("표현식을 입력하면 변환합니다. 예) 255 또는 \"1011 + 1101\"")
            print("설정 변경: :set from N | :set to N  (N은 2~36)")
            continue
        if low.startswith(":set"):
            parts = line.split()
            if len(parts) == 3 and parts[1] in ("from", "to"):
                try:
                    val = int(parts[2])
                    if not (2 <= val <= 36):
                        print("기수는 2~36 범위여야 합니다.")
                        continue
                    if parts[1] == "from":
                        args.base_from = val
                    else:
                        args.base_to = val
                    print(f"설정 변경: from={args.base_from}, to={args.base_to}")
                except ValueError:
                    print("정수를 입력하세요.")
            else:
                print("사용법: :set from N | :set to N")
            continue
        try:
            fmt = _get_format_options(args)
            out, _ = convert(line, args.base_from, args.base_to, args.precision, args.round, fmt)
            print(out)
        except Exception as e:
            print(f"오류: {e}")

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
                print("오류: 배치 모드에서는 --input 인자가 필수입니다.", file=sys.stderr)
                sys.exit(1)
            run_batch(args)
        else:
            if not args.expr:
                # 인자 없는 경우: 대화형 모드로 진입
                repl(args)
            else:
                run_once(args)
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()