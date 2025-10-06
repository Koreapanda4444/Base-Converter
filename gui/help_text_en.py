# gui/help_text_en.py
HELP_TEXT = """📘 Base-Converter Guide (GUI)

[Overview]
- Base converter & calculator (CLI + GUI)
- Mixed-base literals, variables, precision/rounding, significant digits/scientific notation, history, CSV/JSON, theme, portable mode

[Input]
- Single: 1011, A.F, 123.45
- Mixed-base: 0b1010, 0o77, 0xFF, (A.F)_16, 1011_2
- Operators: +, -, *, /, %, ^, parentheses ()
- Assignment: A=0xFF, PI=3.14159

[Bases]
- Select 2~36 in From/To
- Mixed literals override default input base for those tokens

[Precision/Rounding]
- Precision: fractional computation/printing
- Rounding: HALF_UP, HALF_DOWN, HALF_EVEN, CEILING, FLOOR

[Significant digits/Scientific]
- sig: limit total significant digits
- sci: use scientific notation (base 10)

[Result]
- Result field + Copy button

[History]
- Auto save after convert/evaluate
- Columns: Input | Bases | Result | ★ | Tags
- Double-click to re-apply
- Toggle favorite, add tags
- CSV export/import, JSON backup/restore

[Live Validation]
- Inline error message under input

[Theme]
- Adjust text/bg/button/hover colors
- Saved to theme.json

[Portable Mode]
- If portable.flag exists beside the executable, store config/theme/vars/history under local data/ directory

[Shortcuts]
- Enter: Convert
- Esc: Clear
- Ctrl+C: Copy result
- Ctrl+F: Focus history
- F1: This guide

[Examples]
- 0b1011 + (A.F)_16
- A=0xFF, A + 1
- (1011_2 ^ 2) % 0xF
"""

CLI_TEXT = """💻 CLI Guide

[Basic]
python cli/main.py --from 10 --to 2 "255"
python cli/main.py --from 2 --to 16 "1011 + 1101"

[Options]
--from, --to           bases (2~36)
--precision            precision (default 12)
--round                HALF_UP|HALF_DOWN|HALF_EVEN|CEILING|FLOOR
--lower                lowercase output
--group4               group integer part by 4
--underscore           use '_' as group separator
--prefix               print base prefix (0b/0o/0x)
--sci                  scientific notation for base 10
--sig N                significant digits
--batch                batch mode
--input PATH           CSV input
--output PATH          CSV output
--guide                show extended help and exit

[Mixed-base]
- 0b/0o/0x, (..)_base, .._base supported in one expression

[Batch CSV]
expr,base_from,base_to
0b1010+1,2,10
(FF)_16,10,2

[Examples]
python cli/main.py --from 16 --to 2 "FF + 1"
python cli/main.py --precision 20 --round HALF_EVEN --from 10 --to 16 "3.14159"
python cli/main.py --batch --input in.csv --output out.csv
"""
