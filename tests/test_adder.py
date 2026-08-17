"""
Tests for kirby_cost.objects.adder.Adder

Verifies adder cost calculations and the get_double_total() method
used by Modifier.total_value.
"""

import pytest
from tests.conftest import make_adder


class TestAdderBasicCost:
    """Adder total cost is inherited from GenericObject."""

    def test_base_cost_only(self):
        adder = make_adder(base_cost=5.0)
        assert adder.total_cost == 5.0

    def test_zero_cost(self):
        adder = make_adder(base_cost=0.0)
        assert adder.total_cost == 0.0

    def test_negative_cost(self):
        adder = make_adder(base_cost=-3.0)
        assert adder.total_cost == -3.0


class TestAdderRealCost:
    """Adder.real_cost delegates to get_total_cost()."""

    def test_real_equals_total(self):
        adder = make_adder(base_cost=7.0)
        assert adder.real_cost == adder.total_cost


class TestAdderDoubleTotal:
    """
    get_double_total() is used by Modifier.total_value for adder contributions.
    Returns base_cost + level-based costs when selected.
    """

    def test_selected_base_only(self):
        adder = make_adder(base_cost=0.25, selected=True)
        assert adder.double_total() == 0.25

    def test_selected_with_levels(self):
        """Base 0.0 + 3 levels at 0.25 each (level_value=1): 0.75."""
        adder = make_adder(
            base_cost=0.0, levels=3, level_value=1.0, level_cost=0.25, selected=True
        )
        assert adder.double_total() == 0.75

    def test_selected_base_plus_levels(self):
        """Base 0.5 + 2 levels at 0.25 (level_value=1): 0.5 + 0.5 = 1.0."""
        adder = make_adder(
            base_cost=0.5, levels=2, level_value=1.0, level_cost=0.25, selected=True
        )
        assert adder.double_total() == 1.0

    def test_not_selected_no_check(self):
        """When check_selected=False (default), selection doesn't matter."""
        adder = make_adder(base_cost=0.5, selected=False)
        assert adder.double_total() == 0.5

    def test_not_selected_with_check(self):
        """When check_selected=True and not selected, only sub-adders count."""
        adder = make_adder(base_cost=0.5, selected=False)
        # No sub-adders, so total is 0
        assert adder.double_total(check_selected=True) == 0.0

    def test_negative_adder(self):
        """Negative adder value (limitation-like)."""
        adder = make_adder(base_cost=-0.25, selected=True)
        assert adder.double_total() == -0.25

    def test_zero_level_value_skips_levels(self):
        """If level_value is 0, level calculation is skipped."""
        adder = make_adder(
            base_cost=1.0, levels=5, level_value=0.0, level_cost=0.5, selected=True
        )
        assert adder.double_total() == 1.0


class TestAdderProperties:
    """Adder boolean properties."""

    def test_required(self):
        adder = make_adder(required=True)
        assert adder.is_required is True

    def test_not_required(self):
        adder = make_adder(required=False)
        assert adder.is_required is False

    def test_selected(self):
        adder = make_adder(selected=True)
        assert adder.is_selected is True

    def test_not_selected(self):
        adder = make_adder(selected=False)
        assert adder.is_selected is False

    def test_is_custom(self):
        adder = make_adder(xmlid="GENERIC_OBJECT")
        assert adder.custom is True

    def test_not_custom(self):
        adder = make_adder(xmlid="SPECIFIC_ADDER")
        assert adder.custom is False
