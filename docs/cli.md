# Command line

English | [한국어](ko/cli.md)

Install the project with `python -m pip install .`, then use `radixscope` or
`python -m radixscope`. Every command supports `--help` and `--json`.

```sh
radixscope convert FF --from 16 --to 2 8 10 16
radixscope convert "0.(3)" --to 2 10 --precision 8 --rounding half-even
radixscope expression "0x10 + 2#11 / 10#2" --to 2 10 16
radixscope trace "1/3" --from 10 --to 2 --json
radixscope integer -128 --width 8 --signed --op shr --operand 1
radixscope integer 127 --width 8 --signed --op add --operand 1 --json
radixscope integer FF --base 16 --width 8 --signed --pattern
radixscope ieee decode 3F800000 --width 32
radixscope ieee encode "1/10" --width 32 --json
radixscope ieee encode nan --width 64 --payload 123 --signaling
radixscope ieee encode 0 --negative-zero --width 32
```

Conversion defaults to source base 10 and target bases 2, 8, 10 and 16. Exact output
uses parentheses for recurring digits. `--precision` requests a fixed number of
fractional digits with truncate, half-up, half-even, floor or ceiling rounding.
Trace output lists division and multiplication steps and the recurring start position.

Integer input is a mathematical value unless `--pattern` is selected. Signed values
use two's complement. Arithmetic reports both the exact result and whether it overflowed,
and explicitly displays the wrapped result. Bitwise operands share the selected base,
width and signedness; shift counts are decimal. Endian order affects the byte preview.

IEEE encode accepts exact mixed-base expressions, `nan`, `inf` and `infinity` with an
optional sign. Decode reads a raw integer in base 16 by default. NaN payload and signaling
options apply only to NaN encoding. Raw decode preserves payloads without host-float conversion.

Successful commands return 0. Invalid arguments or numbers return 2, write a short error
to stderr and leave stdout empty. Negative values that look like options, such as `-FF`
or `-inf`, must follow `--`; place all command options before that separator.
For example: `radixscope ieee encode --width 32 -- -inf`.
