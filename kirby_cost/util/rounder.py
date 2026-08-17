"""
Rounding utilities for Hero Designer cost calculations.

Converted from com.hero.util.Rounder.java
Uses Python's Decimal for precision matching the Java oracle's BigDecimal behavior.
"""

from decimal import Decimal, ROUND_HALF_DOWN, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
from typing import Optional


# Default number of digits for rounding (can be configured)
# Hero Designer default is 2 (set in HeroDesigner.java line 284)
_DEFAULT_ROUNDING_DIGITS = 2


def rounding_digits(digits: int) -> None:
    """Set the number of digits for rounding calculations."""
    global _DEFAULT_ROUNDING_DIGITS
    _DEFAULT_ROUNDING_DIGITS = digits


def get_rounding_digits() -> int:
    """Get the current number of digits for rounding calculations."""
    return _DEFAULT_ROUNDING_DIGITS


def round_down(value: float) -> int:
    """
    Round down (floor) to nearest integer.

    Matches Java Rounder.roundDown — always rounds toward negative infinity.

    Args:
        value: Value to round

    Returns:
        Rounded integer value

    Example:
        round_down(5.9)  ->  5
        round_down(-5.9) -> -6
    """
    import math
    return math.floor(value)


def round_half_down(value: float, rounding_digits: Optional[int] = None) -> int:
    """
    Round half down to nearest integer.

    This is the primary rounding method used for Active Cost and Real Cost
    calculations in Hero Designer.

    Process:
    1. Round iteratively from highest to lowest digit
    2. Add epsilon (1.0E-11) before rounding
    3. Subtract epsilon (1.0E-10) after rounding
    4. Final round uses ROUND_HALF_DOWN (rounds 0.5 down)

    Args:
        value: Value to round
        rounding_digits: Number of decimal places to use (defaults to global setting)

    Returns:
        Rounded integer value

    Example:
        round_half_down(10.5) -> 10  # 0.5 rounds down
        round_half_down(10.6) -> 11  # > 0.5 rounds up
    """
    if rounding_digits is None:
        rounding_digits = _DEFAULT_ROUNDING_DIGITS

    d = float(value)

    # If only 1 digit, round directly
    # Java: new BigDecimal(d + 1.0E-11).setScale(n, 1) where 1=ROUND_DOWN
    if rounding_digits <= 1:
        decimal = Decimal(str(d + 1.0E-11))
        decimal = decimal.quantize(Decimal('0.1') ** rounding_digits, rounding=ROUND_DOWN)
        d = float(decimal)
    else:
        # Round iteratively from highest to lowest digit
        n = rounding_digits
        while n > 1:
            d = _round_half_down_iterative(d, n)
            n -= 1

    # Final round to integer using ROUND_HALF_DOWN
    decimal = Decimal(str(d))
    decimal = decimal.quantize(Decimal('1'), rounding=ROUND_HALF_DOWN)
    return int(decimal)


def _round_half_down_iterative(value: float, digits: int) -> float:
    """
    Internal helper for iterative rounding.

    Args:
        value: Value to round
        digits: Number of decimal places

    Returns:
        Rounded value with one less decimal place
    """
    # Add epsilon before rounding
    # Java: new BigDecimal(d + 1.0E-11).setScale(n, 1) where 1=ROUND_DOWN
    decimal = Decimal(str(value + 1.0E-11))
    decimal = decimal.quantize(Decimal('0.1') ** digits, rounding=ROUND_DOWN)

    # Subtract epsilon after rounding
    # Java: setScale(n-1, 5) where 5=ROUND_HALF_DOWN
    decimal = Decimal(str(float(decimal) - 1.0E-10))
    decimal = decimal.quantize(Decimal('0.1') ** (digits - 1), rounding=ROUND_HALF_DOWN)

    return float(decimal)


def round_half_up(value: float, rounding_digits: Optional[int] = None) -> int:
    """
    Round half up to nearest integer.

    Used for END Cost display values in Hero Designer.

    Process:
    1. Round iteratively from highest to lowest digit
    2. Add epsilon (1.0E-10) after rounding
    3. Final round uses ROUND_HALF_UP (rounds 0.5 up)

    Args:
        value: Value to round
        rounding_digits: Number of decimal places to use (defaults to global setting)

    Returns:
        Rounded integer value

    Example:
        round_half_up(10.5) -> 11  # 0.5 rounds up
        round_half_up(10.4) -> 10  # < 0.5 rounds down
    """
    if rounding_digits is None:
        rounding_digits = _DEFAULT_ROUNDING_DIGITS

    d = float(value)

    # If only 1 digit, round directly
    if rounding_digits <= 1:
        decimal = Decimal(str(d))
        decimal = decimal.quantize(Decimal('0.1') ** rounding_digits, rounding=ROUND_HALF_UP)
        d = float(decimal)
    else:
        # Round iteratively from highest to lowest digit
        n = rounding_digits
        while n > 1:
            d = _round_half_up_iterative(d, n)
            n -= 1

    # Final round to integer using ROUND_HALF_UP
    decimal = Decimal(str(d))
    decimal = decimal.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(decimal)


def _round_half_up_iterative(value: float, digits: int) -> float:
    """
    Internal helper for iterative rounding (half up).

    Args:
        value: Value to round
        digits: Number of decimal places

    Returns:
        Rounded value with one less decimal place
    """
    # Round to specified digits
    decimal = Decimal(str(value))
    decimal = decimal.quantize(Decimal('0.1') ** digits, rounding=ROUND_HALF_UP)

    # Add epsilon after rounding
    decimal = Decimal(str(float(decimal) + 1.0E-10))
    decimal = decimal.quantize(Decimal('0.1') ** (digits - 1), rounding=ROUND_HALF_UP)

    return float(decimal)


def round_up(value: float) -> int:
    """
    Round up (ceil) to nearest integer.

    Matches Java Rounder.roundUp — always rounds toward positive infinity.

    Args:
        value: Value to round

    Returns:
        Rounded integer value

    Example:
        round_up(5.1)  ->  6
        round_up(-5.1) -> -5
    """
    import math
    return math.ceil(value)


def round_to_quarter(value: float) -> float:
    """
    Round to nearest quarter (0.25).

    Used for modifier values in Hero Designer.
    Multiply by 4, round to integer (half-up), divide by 4.

    Args:
        value: Value to round

    Returns:
        Value rounded to nearest 0.25

    Example:
        round_to_quarter(0.3)  -> 0.25
        round_to_quarter(0.4)  -> 0.5
        round_to_quarter(0.13) -> 0.25
    """
    scaled = Decimal(str(value)) * 4
    rounded = scaled.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return float(rounded / 4)
