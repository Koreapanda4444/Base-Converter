# RadixScope v2 specification

## Core rules

- Supported bases are 2 through 36.
- Input digits are case-insensitive. Formatted output uses uppercase letters.
- Core arithmetic is exact and does not use binary floating-point values.
- Leading and trailing whitespace is ignored. Internal whitespace is invalid.
- Every digit must be valid for the selected base.
- Zero is always normalized to a positive sign.

## Digit alphabet

Digit values use the following alphabet:

```text
0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

`A` represents 10 and `Z` represents 35.

## Input forms

`parse_number` takes the base separately. `parse_literal` reads the base from the numeric text.

```text
sign      = "+" | "-"
integer   = sign? digit+
finite    = sign? digit+ "." digit+
ratio     = integer "/" integer
recurring = sign? digit+ "." digit* "(" digit+ ")"
number    = ratio | recurring | finite | integer
```

Examples:

| Input | Base | Exact value |
| --- | ---: | ---: |
| `-101` | 2 | `-5` |
| `A.F` | 16 | `175/16` |
| `1/3` | 10 | `1/3` |
| `A/10` | 16 | `5/8` |
| `0.(3)` | 10 | `1/3` |
| `0.1(6)` | 10 | `1/6` |
| `0.(01)` | 2 | `1/3` |

Both sides of a ratio use the selected base. A zero denominator is invalid.

## Exact value model

Every accepted number is normalized to a rational value:

- numerator and denominator are reduced by their greatest common divisor;
- the denominator is always positive;
- integer values use denominator `1`;
- equivalent inputs produce the same exact value.

## Conversion behavior

- Integer conversion uses the complete exact value.
- Fractional conversion tracks remainders so recurring sections can be detected.
- A terminating result contains no recurring section.
- A recurring result uses parentheses, such as `0.(3)`.
- Precision limits and rounding affect only formatted output, never the stored exact value.
- Converting a complete recurring representation back to a value must reproduce the original rational value.

## Mixed-base literals

Unprefixed literals use base 10. Prefixes `0b`, `0o` and `0x` select bases 2, 8 and 16;
prefixes and digits are case-insensitive. `base#digits` selects any base from 2 through 36,
with the base label always written in decimal. Finite and recurring fractions use the same
syntax as `parse_number`: `0xA.F`, `2#0.(01)` and `0.1(6)` are exact values.
An integer part is required; `.5` and `0x.F` are not accepted. Scientific notation is unsupported.

`parse_literal` accepts an optional leading sign and outer whitespace for a single literal.
In expressions, signs are unary operators. The slash is always division between two literals,
each with its own base: `0xA / 10` is `1`, while `0xA / 16#10` is `5/8`.
For a standalone same-base ratio, use `parse_number("A/10", 16)` instead.

```python
from radixscope.core import ExactValue, evaluate_expression, parse_literal

assert parse_literal("0xA.F") == ExactValue(175, 16)
assert evaluate_expression("0xFF + 0b10") == ExactValue(257)
assert evaluate_expression("16#FF + 2#10") == ExactValue(257)
assert evaluate_expression("(0x10 + 2) ** -2") == ExactValue(1, 324)
```

## Expression tokenization

`tokenize_expression` separates numeric literals, operators and grouping parentheses.
Each immutable token carries its kind, original text and zero-based half-open source span.
An end token marks the end of the input. Whitespace between tokens is ignored;
whitespace within a literal is not allowed. Literal digits and base labels use ASCII.
Signs are separate tokens, and recurring parentheses belong to their numeric literal.
The `**` operator is emitted as one power token rather than two multiplication tokens.

## Expression parsing and evaluation

`parse_expression` returns an immutable tree of literal, unary and binary nodes.
`evaluate_parsed_expression` evaluates that tree, and `evaluate_expression` combines both.
All literals and intermediate results remain exact rational values.

```text
expression = product (("+" | "-") product)*
product    = unary (("*" | "/") unary)*
unary      = ("+" | "-") unary | power
power      = primary ("**" unary)?
primary    = literal | "(" expression ")"
```

Addition, subtraction, multiplication and division associate left to right.
Power associates right to left: `10#2**10#3**10#2` is `512`.
Power binds tighter than a leading sign: `-10#2**10#2` is `-4`.
Exponents must evaluate to integers; negative exponents produce exact reciprocals.
Zero to a negative power and division by zero are invalid. Zero to the zeroth power is `1`.
Errors identify the operator or token position; excessive nesting raises a domain error.
Variable names, assignments, function calls and implicit multiplication are not supported.

## Fixed-width integer model

`FixedWidthInteger(value, width, signed=False)` stores an immutable integer with an explicit
positive bit width. Unsigned bounds are `0` through `2**width - 1`; signed bounds are
`-2**(width - 1)` through `2**(width - 1) - 1`. Construction checks this range.
Widths need not be multiples of eight. Boolean and non-integer values are rejected.

`from_exact` and `from_text` connect the model to the rational core and numeric parser.
Fractional values are rejected instead of truncated. The `exact` property returns the
mathematical value as an `ExactValue`. `resize` preserves that value and signedness,
checking the destination range instead of wrapping or discarding bits.

## Signed and unsigned interpretation

`bit_pattern` and `bits` encode a fixed-width value without a leading minus sign.
`reinterpret(signed=...)` preserves the width and every bit, changing only its interpretation.
`interpret_bit_pattern` reports the unsigned value, signed two's-complement value,
sign bit, padded binary text and uppercase hexadecimal text for the same pattern.

`from_bits` uses the raw binary text length when no width is supplied. A larger explicit
width zero-extends the pattern before signed interpretation; extra textual bits are rejected.
Thus `11111111` is signed `-1` at eight bits, but signed `255` at sixteen bits.
`parse_bit_pattern` reads integer digits in a specified base and then interprets the pattern.
`from_text` instead reads a mathematical value, so signed `-1` and pattern `FF` are
different input paths. Neither path silently wraps out-of-range input.

## Range and overflow analysis

`analyze_range` preserves the mathematical integer and reports its destination bounds.
`overflowed` indicates whether it fits. `checked` raises `IntegerRangeError` on overflow,
while `wrapped` explicitly reduces the result modulo `2**width` and decodes its signedness.
The exact result is never overwritten by the wrapped result.

`analyze_arithmetic` analyzes addition, subtraction and multiplication of two fixed-width
operands with identical width and signedness. Signed and unsigned overflow are detected
against their respective mathematical ranges. For example, signed eight-bit `127 + 1`
has exact result `128`, overflows, and wraps to `-128`; unsigned `255 + 1` wraps to `0`.
Operands with different formats must be explicitly resized or reinterpreted first.

## Errors

The core rejects:

- bases outside 2 through 36;
- empty input or a sign without digits;
- digits that do not exist in the selected base;
- multiple decimal points, fraction separators, or recurring groups;
- empty recurring groups;
- zero denominators;
- malformed literal prefixes, invalid base labels and unsupported numeric syntax.
