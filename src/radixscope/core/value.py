from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class ExactValue:
    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        value = Fraction(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", value.numerator)
        object.__setattr__(self, "denominator", value.denominator)

    @classmethod
    def from_fraction(cls, value: Fraction) -> ExactValue:
        return cls(value.numerator, value.denominator)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)

    @property
    def is_integer(self) -> bool:
        return self.denominator == 1

    @property
    def sign(self) -> int:
        return (self.numerator > 0) - (self.numerator < 0)

    def reciprocal(self) -> ExactValue:
        if self.numerator == 0:
            raise ZeroDivisionError("zero has no reciprocal")
        return ExactValue(self.denominator, self.numerator)

    def __add__(self, other: ExactValue) -> ExactValue:
        return ExactValue.from_fraction(self.fraction + other.fraction)

    def __sub__(self, other: ExactValue) -> ExactValue:
        return ExactValue.from_fraction(self.fraction - other.fraction)

    def __mul__(self, other: ExactValue) -> ExactValue:
        return ExactValue.from_fraction(self.fraction * other.fraction)

    def __truediv__(self, other: ExactValue) -> ExactValue:
        return ExactValue.from_fraction(self.fraction / other.fraction)

    def __pow__(self, exponent: int) -> ExactValue:
        return ExactValue.from_fraction(self.fraction**exponent)

    def __neg__(self) -> ExactValue:
        return ExactValue(-self.numerator, self.denominator)

    def __abs__(self) -> ExactValue:
        return ExactValue(abs(self.numerator), self.denominator)

    def __str__(self) -> str:
        if self.is_integer:
            return str(self.numerator)
        return f"{self.numerator}/{self.denominator}"
