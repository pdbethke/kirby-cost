"""
Tests for kirby_cost.util.rounder

Verifies Python rounding matches the Java oracle's BigDecimal behavior exactly.
Reference: HD6_SOURCE_CODE_FORMULAS.md - Rounding Rules section.
"""

import pytest
from kirby_cost.util.rounder import (
    round_down,
    round_half_down,
    round_half_up,
    round_up,
    round_to_quarter,
    rounding_digits,
    get_rounding_digits,
)


class TestRoundDown:
    """round_down: toward zero for both positive and negative values."""

    def test_positive_integer(self):
        assert round_down(5.0) == 5

    def test_positive_rounds_down(self):
        assert round_down(5.9) == 5

    def test_positive_just_above(self):
        assert round_down(5.1) == 5

    def test_positive_half(self):
        assert round_down(5.5) == 5

    def test_negative_rounds_toward_neg_infinity(self):
        # Negative values round toward negative infinity (floor)
        assert round_down(-5.9) == -6

    def test_negative_half(self):
        assert round_down(-5.5) == -6

    def test_zero(self):
        assert round_down(0.0) == 0

    def test_already_integer(self):
        assert round_down(10.0) == 10


class TestRoundHalfDown:
    """round_half_down: 0.5 rounds DOWN. Primary rounding for Active/Real Cost."""

    def test_exact_half_rounds_down(self):
        """HD6 rule: 10.5 -> 10 (half rounds down)."""
        assert round_half_down(10.5) == 10

    def test_above_half_rounds_up(self):
        """10.6 -> 11."""
        assert round_half_down(10.6) == 11

    def test_below_half_rounds_down(self):
        """10.4 -> 10."""
        assert round_half_down(10.4) == 10

    def test_integer_unchanged(self):
        assert round_half_down(10.0) == 10

    def test_zero(self):
        assert round_half_down(0.0) == 0

    def test_one(self):
        assert round_half_down(1.0) == 1

    # --- Champions 6E real-world calculations ---

    def test_energy_blast_active_cost(self):
        """10d6 EB (50pts) with +1 advantage = 50 * 2.0 = 100."""
        assert round_half_down(100.0) == 100

    def test_active_cost_with_half_advantage(self):
        """50 * 1.5 = 75 exactly."""
        assert round_half_down(75.0) == 75

    def test_real_cost_quarter_limitation(self):
        """100 / 1.25 = 80 exactly."""
        assert round_half_down(80.0) == 80

    def test_real_cost_half_limitation(self):
        """100 / 1.5 = 66.666... -> 67."""
        assert round_half_down(100.0 / 1.5) == 67

    def test_real_cost_one_limitation(self):
        """100 / 2.0 = 50 exactly."""
        assert round_half_down(50.0) == 50

    def test_real_cost_two_limitation(self):
        """100 / 3.0 = 33.333... -> 33."""
        assert round_half_down(100.0 / 3.0) == 33

    def test_awkward_fraction(self):
        """75 / 1.75 = 42.857... -> 43."""
        assert round_half_down(75.0 / 1.75) == 43

    def test_exactly_half_from_division(self):
        """50 / 1.0 + some calc that yields 0.5 exactly."""
        assert round_half_down(50.5) == 50

    def test_small_value_rounds_to_zero(self):
        """0.4 -> 0."""
        assert round_half_down(0.4) == 0

    def test_large_value(self):
        """200.5 -> 200 (half rounds down)."""
        assert round_half_down(200.5) == 200

    def test_large_value_above_half(self):
        """200.6 -> 201."""
        assert round_half_down(200.6) == 201


class TestRoundHalfUp:
    """round_half_up: 0.5 rounds UP. Used for modifier values and END cost display."""

    def test_exact_half_rounds_up(self):
        """HD6 rule: 10.5 -> 11 (half rounds up)."""
        assert round_half_up(10.5) == 11

    def test_above_half_rounds_up(self):
        assert round_half_up(10.6) == 11

    def test_below_half_rounds_down(self):
        assert round_half_up(10.4) == 10

    def test_integer_unchanged(self):
        assert round_half_up(10.0) == 10

    def test_zero(self):
        assert round_half_up(0.0) == 0

    def test_modifier_quarter_precision(self):
        """Modifier value * 4 = 2.0 -> 2 (used in quarter rounding)."""
        assert round_half_up(2.0) == 2

    def test_modifier_quarter_half(self):
        """0.5 * 4 = 2.0 -> 2."""
        assert round_half_up(2.0) == 2


class TestRoundUp:
    """round_up: always away from zero."""

    def test_positive_rounds_up(self):
        assert round_up(5.1) == 6

    def test_positive_just_above(self):
        assert round_up(5.01) == 6

    def test_positive_half(self):
        assert round_up(5.5) == 6

    def test_positive_integer(self):
        assert round_up(5.0) == 5

    def test_negative_rounds_toward_pos_infinity(self):
        # Negative: rounds toward positive infinity (ceil)
        assert round_up(-5.9) == -5

    def test_negative_half(self):
        assert round_up(-5.5) == -5

    def test_zero(self):
        assert round_up(0.0) == 0


class TestRoundToQuarter:
    """round_to_quarter: used for modifier values (0.25 precision)."""

    def test_exact_quarter(self):
        assert round_to_quarter(0.25) == 0.25

    def test_exact_half(self):
        assert round_to_quarter(0.5) == 0.5

    def test_exact_three_quarter(self):
        assert round_to_quarter(0.75) == 0.75

    def test_rounds_up_to_quarter(self):
        """0.13 -> 0.25 (nearest quarter)."""
        assert round_to_quarter(0.13) == 0.25

    def test_rounds_down_to_zero(self):
        """0.12 -> 0.0 (nearest quarter)."""
        assert round_to_quarter(0.12) == 0.0

    def test_rounds_to_half(self):
        """0.4 -> 0.5."""
        assert round_to_quarter(0.4) == 0.5

    def test_rounds_down_to_quarter(self):
        """0.3 -> 0.25."""
        assert round_to_quarter(0.3) == 0.25

    def test_integer(self):
        assert round_to_quarter(1.0) == 1.0

    def test_one_and_quarter(self):
        assert round_to_quarter(1.25) == 1.25

    def test_negative_quarter(self):
        """Negative modifier values."""
        assert round_to_quarter(-0.25) == -0.25

    def test_negative_half(self):
        assert round_to_quarter(-0.5) == -0.5

    def test_negative_rounds(self):
        """-.3 -> -0.25."""
        assert round_to_quarter(-0.3) == -0.25

    def test_zero(self):
        assert round_to_quarter(0.0) == 0.0


class TestRoundingDigitsConfig:
    """Verify global rounding digits can be changed."""

    def test_default_digits(self):
        assert get_rounding_digits() == 2  # Java default (HeroDesigner.java line 284)

    def test_set_and_get(self):
        original = get_rounding_digits()
        try:
            rounding_digits(3)
            assert get_rounding_digits() == 3
        finally:
            rounding_digits(original)

    def test_multi_digit_rounding(self):
        """With more rounding digits, iterative rounding kicks in."""
        original = get_rounding_digits()
        try:
            rounding_digits(3)
            # Should still produce correct integer results
            result = round_half_down(10.5)
            assert isinstance(result, int)
            assert result == 10
        finally:
            rounding_digits(original)
