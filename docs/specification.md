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

The base is supplied separately from the numeric text during the initial core implementation.

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

## Errors

The core rejects:

- bases outside 2 through 36;
- empty input or a sign without digits;
- digits that do not exist in the selected base;
- multiple decimal points, fraction separators, or recurring groups;
- empty recurring groups;
- zero denominators;
- unsupported prefixes or mixed-base syntax before those features are introduced.
