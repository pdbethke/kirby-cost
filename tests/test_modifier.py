"""
Tests for kirby_cost.objects.modifier.Modifier

Verifies modifier value calculation including:
  - Base value (positive = advantage, negative = limitation)
  - Adder contributions
  - Level-based costs
  - Nested modifiers (modifiers on modifiers)
  - Quarter-precision rounding
  - Min/max limits

Reference: HD6_SOURCE_CODE_FORMULAS.md - section 4 (getTotalValue).
"""

import pytest
from tests.conftest import make_modifier, make_adder


# ═══════════════════════════════════════════════════════════
#  get_total_value() — basic
# ═══════════════════════════════════════════════════════════

class TestModifierBasicValue:
    """Simple modifier value is just the base cost."""

    def test_positive_advantage(self):
        """A +1/2 advantage."""
        mod = make_modifier(base_cost=0.5)
        assert mod.total_value == 0.5

    def test_full_advantage(self):
        """A +1 advantage."""
        mod = make_modifier(base_cost=1.0)
        assert mod.total_value == 1.0

    def test_quarter_advantage(self):
        """A +1/4 advantage."""
        mod = make_modifier(base_cost=0.25)
        assert mod.total_value == 0.25

    def test_negative_limitation(self):
        """A -1/4 limitation."""
        mod = make_modifier(base_cost=-0.25)
        assert mod.total_value == -0.25

    def test_half_limitation(self):
        """A -1/2 limitation."""
        mod = make_modifier(base_cost=-0.5)
        assert mod.total_value == -0.5

    def test_full_limitation(self):
        """A -1 limitation."""
        mod = make_modifier(base_cost=-1.0)
        assert mod.total_value == -1.0

    def test_zero_modifier(self):
        """A 0-value modifier (e.g., duration change with no cost)."""
        mod = make_modifier(base_cost=0.0)
        assert mod.total_value == 0.0


# ═══════════════════════════════════════════════════════════
#  get_total_value() — with adders
# ═══════════════════════════════════════════════════════════

class TestModifierWithAdders:
    """Adders add to the modifier's base value."""

    def test_adder_increases_value(self):
        """Base +0.25 plus +0.25 adder = +0.5."""
        mod = make_modifier(base_cost=0.25)
        adder = make_adder(base_cost=0.25, selected=True)
        mod.assigned_adders = [adder]
        assert mod.total_value == 0.5

    def test_adder_on_limitation(self):
        """Base -0.25 plus -0.25 adder = -0.5."""
        mod = make_modifier(base_cost=-0.25)
        adder = make_adder(base_cost=-0.25, selected=True)
        mod.assigned_adders = [adder]
        assert mod.total_value == -0.5

    def test_multiple_adders(self):
        """Base 0.5 + adder 0.25 + adder 0.25 = 1.0."""
        mod = make_modifier(base_cost=0.5)
        a1 = make_adder(base_cost=0.25, selected=True)
        a2 = make_adder(base_cost=0.25, selected=True)
        mod.assigned_adders = [a1, a2]
        assert mod.total_value == 1.0


# ═══════════════════════════════════════════════════════════
#  get_total_value() — with levels
# ═══════════════════════════════════════════════════════════

class TestModifierWithLevels:
    """Level-based modifier costs: (levels / level_value) * level_cost."""

    def test_leveled_advantage(self):
        """Base 0.25 with 2 levels at 0.25 each: 0.25 + (2/1)*0.25 = 0.75."""
        mod = make_modifier(base_cost=0.25, levels=2, level_value=1.0, level_cost=0.25)
        assert mod.total_value == 0.75

    def test_leveled_limitation(self):
        """Base -0.25 with 1 level at -0.25: -0.25 + (1/1)*(-0.25) = -0.5."""
        mod = make_modifier(base_cost=-0.25, levels=1, level_value=1.0, level_cost=-0.25)
        assert mod.total_value == -0.5


# ═══════════════════════════════════════════════════════════
#  get_total_value() — nested modifiers
# ═══════════════════════════════════════════════════════════

class TestModifierNesting:
    """Modifiers can have sub-modifiers (advantages on limitations, etc.)."""

    def test_advantage_on_advantage(self):
        """
        Base +0.5 advantage with a +0.5 sub-advantage.
        value = 0.5 * (1 + 0.5) = 0.75
        """
        mod = make_modifier(base_cost=0.5)
        sub = make_modifier(base_cost=0.5, xmlid="SUB_ADV")
        mod.assigned_modifiers = [sub]
        assert mod.total_value == 0.75

    def test_limitation_on_advantage(self):
        """
        Base +1.0 advantage with a -0.5 sub-limitation.
        value = 1.0 / (1 + 0.5) = 0.666... -> round to quarter -> 0.75
        """
        mod = make_modifier(base_cost=1.0)
        sub = make_modifier(base_cost=-0.5, xmlid="SUB_LIM")
        mod.assigned_modifiers = [sub]
        assert mod.total_value == 0.75

    def test_advantage_on_limitation(self):
        """
        Base -1.0 limitation with a +0.5 sub-advantage.
        value = -1.0 * (1 + 0.5) = -1.5
        Quarter rounding: |-1.5| * 4 = 6.0, round(6) = 6, /4 = 1.5, * -1 = -1.5
        """
        mod = make_modifier(base_cost=-1.0)
        sub = make_modifier(base_cost=0.5, xmlid="SUB_ADV")
        mod.assigned_modifiers = [sub]
        assert mod.total_value == -1.5

    def test_limitation_on_limitation(self):
        """
        Base -1.0 limitation with a -0.25 sub-limitation.
        The sub-limitation is negative, so it divides:
        value = -1.0 / (1 + 0.25) = -0.8 -> round to quarter -> -0.75
        """
        mod = make_modifier(base_cost=-1.0)
        sub = make_modifier(base_cost=-0.25, xmlid="SUB_LIM")
        mod.assigned_modifiers = [sub]
        assert mod.total_value == -0.75


# ═══════════════════════════════════════════════════════════
#  get_total_value() — quarter rounding
# ═══════════════════════════════════════════════════════════

class TestModifierQuarterRounding:
    """Values are rounded to nearest 1/4 (0.25 precision)."""

    def test_already_on_quarter(self):
        mod = make_modifier(base_cost=0.75)
        assert mod.total_value == 0.75

    def test_rounds_to_nearest_quarter(self):
        """
        1.0 / (1 + 0.5) = 0.666...
        0.666 * 4 = 2.666, round_half_up = 3, /4 = 0.75
        """
        mod = make_modifier(base_cost=1.0)
        sub = make_modifier(base_cost=-0.5, xmlid="SUB")
        mod.assigned_modifiers = [sub]
        assert mod.total_value == 0.75


# ═══════════════════════════════════════════════════════════
#  get_total_value() — min/max limits
# ═══════════════════════════════════════════════════════════

class TestModifierMinMax:
    """Modifier values are clamped to min/max range."""

    def test_max_limit_enforced(self):
        """Value exceeds max: capped."""
        mod = make_modifier(base_cost=5.0, max_cost=2.0, max_set=True)
        assert mod.total_value == 2.0

    def test_min_limit_enforced(self):
        """Value below min: capped."""
        mod = make_modifier(base_cost=-5.0, minimum_cost=-2.0, min_set=True)
        assert mod.total_value == -2.0

    def test_default_range(self):
        """Default range is -10 to +10."""
        mod = make_modifier(base_cost=0.5)
        assert mod.minimum_cost == -10.0
        assert mod.max_cost == 10.0


# ═══════════════════════════════════════════════════════════
#  is_limitation_modifier()
# ═══════════════════════════════════════════════════════════

class TestIsLimitation:
    """Determines if a modifier is a limitation based on its value."""

    def test_positive_is_not_limitation(self):
        mod = make_modifier(base_cost=0.5)
        assert mod.limitation_modifier is False

    def test_negative_is_limitation(self):
        mod = make_modifier(base_cost=-0.5)
        assert mod.limitation_modifier is True

    def test_zero_is_not_limitation(self):
        mod = make_modifier(base_cost=0.0)
        assert mod.limitation_modifier is False

    def test_negative_adder_makes_limitation(self):
        """Modifier with negative adder and no base is a limitation."""
        mod = make_modifier(base_cost=0.0)
        adder = make_adder(base_cost=-0.25)
        mod.assigned_adders = [adder]
        assert mod.limitation_modifier is True

    def test_positive_adder_not_limitation(self):
        mod = make_modifier(base_cost=0.0)
        adder = make_adder(base_cost=0.25)
        mod.assigned_adders = [adder]
        assert mod.limitation_modifier is False


# ═══════════════════════════════════════════════════════════
#  Modifier included() — type/duration checking
# ═══════════════════════════════════════════════════════════

class TestModifierInclusion:
    """Modifier.included() checks if modifier can apply to an object."""

    def test_no_restrictions(self):
        """Modifier with no type or duration restriction allows anything."""
        mod = make_modifier()
        from tests.conftest import make_object
        obj = make_object()
        assert mod.included(obj) == ""

    def test_none_object(self):
        """None object always allowed."""
        mod = make_modifier()
        assert mod.included(None) == ""

    def test_duration_instant_restriction(self):
        """Modifier restricted to INSTANT powers rejects CONSTANT powers."""
        mod = make_modifier()
        mod.duration = "INSTANT"
        from tests.conftest import make_object
        obj = make_object(duration="CONSTANT")
        result = mod.included(obj)
        assert "Instant" in result

    def test_duration_instant_allows_instant(self):
        mod = make_modifier()
        mod.duration = "INSTANT"
        from tests.conftest import make_object
        obj = make_object(duration="INSTANT")
        assert mod.included(obj) == ""
