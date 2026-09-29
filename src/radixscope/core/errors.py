class RadixScopeError(ValueError):
    pass


class InvalidBaseError(RadixScopeError):
    pass


class InvalidDigitError(RadixScopeError):
    pass


class InvalidNumberError(RadixScopeError):
    pass


class InvalidExpressionError(RadixScopeError):
    pass


class InvalidWidthError(RadixScopeError):
    pass


class IntegerRangeError(RadixScopeError):
    pass


class NonIntegerValueError(RadixScopeError):
    pass
