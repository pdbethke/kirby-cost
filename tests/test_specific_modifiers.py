"""
Tests for specific modifier subclasses.

Validates that each modifier:
  1. Imports and instantiates correctly
  2. Has correct XMLID
  3. Calculates correct total_value
  4. Has correct is_limitation behavior
  5. Overrides getTotalValue correctly (for modifiers with custom logic)
  6. Validates included() correctly (for modifiers with custom validation)
"""

import pytest
from tests.conftest import make_object, make_modifier, make_adder


# ═══════════════════════════════════════════════════════════
#  Import all modifier classes
# ═══════════════════════════════════════════════════════════

class TestModifierImports:
    """All 98 modifier classes import without error."""

    def test_all_modifiers_import(self):
        """Every modifier class the registry knows is exported from the package.

        Used to be `assert len(m.__all__) == 98` -- a count that went stale
        the moment a class was deleted (2026-08-29, the 5E-only modifiers).
        The property actually wanted is that no registered modifier is
        missing from `__all__`, so that is what is asserted; the number is
        derived, not remembered.
        """
        import kirby_cost.objects.modifiers as m
        import kirby_cost.objects._registry_imports  # noqa: F401 -- full registry
        from kirby_cost.objects.base import GenericObject
        registered = {c.__name__ for c in GenericObject._registry.values()
                      if c.__module__.startswith("kirby_cost.objects.modifiers.")}
        assert registered, "registry holds no modifier classes -- import order broke"
        missing = sorted(registered - set(m.__all__))
        assert missing == [], f"registered but not exported: {missing}"

    def test_key_advantages_import(self):
        from kirby_cost.objects.modifiers import (
            ArmorPiercing, AreaEffect, Autofire, Cumulative,
            Hardened, Indirect, Invisible, Penetrating,
            Ranged, ReducedEND, UsableOnOthers,
        )

    def test_key_limitations_import(self):
        from kirby_cost.objects.modifiers import (
            AlwaysOn, Charges, Concentration,
            CostsEND, ExtraTime, Focus, Gestures,
            Incantations, IncreasedEND, Linked,
            RequiresSkillRoll, SideEffects, TimeLimit,
        )


# ═══════════════════════════════════════════════════════════
#  Simple Advantages — instantiation and XMLID
# ═══════════════════════════════════════════════════════════

class TestSimpleAdvantages:
    """Simple advantages that don't override getTotalValue."""

    def test_hardened(self):
        from kirby_cost.objects.modifiers import Hardened
        mod = Hardened()
        assert mod.XMLID == "HARDENED"
        assert mod.xmlid == "HARDENED"

    def test_armor_piercing(self):
        from kirby_cost.objects.modifiers import ArmorPiercing
        mod = ArmorPiercing()
        assert mod.XMLID == "ARMORPIERCING"

    def test_penetrating(self):
        from kirby_cost.objects.modifiers import Penetrating
        mod = Penetrating()
        assert mod.XMLID == "PENETRATING"

    def test_ranged(self):
        from kirby_cost.objects.modifiers import Ranged
        mod = Ranged()
        assert mod.XMLID == "RANGED"

    def test_indirect(self):
        from kirby_cost.objects.modifiers import Indirect
        mod = Indirect()
        assert mod.XMLID == "INDIRECT"

    def test_cumulative(self):
        from kirby_cost.objects.modifiers import Cumulative
        mod = Cumulative()
        assert mod.XMLID == "CUMULATIVE"


# ═══════════════════════════════════════════════════════════
#  Simple Limitations — instantiation and XMLID
# ═══════════════════════════════════════════════════════════

class TestSimpleLimitations:

    def test_focus(self):
        from kirby_cost.objects.modifiers import Focus
        mod = Focus()
        assert mod.XMLID == "FOCUS"

    def test_gestures(self):
        from kirby_cost.objects.modifiers import Gestures
        mod = Gestures()
        assert mod.XMLID == "GESTURES"

    def test_incantations(self):
        from kirby_cost.objects.modifiers import Incantations
        mod = Incantations()
        assert mod.XMLID == "INCANTATIONS"

    def test_concentration(self):
        from kirby_cost.objects.modifiers import Concentration
        mod = Concentration()
        assert mod.XMLID == "CONCENTRATION"

    def test_extra_time(self):
        from kirby_cost.objects.modifiers import ExtraTime
        mod = ExtraTime()
        assert mod.XMLID == "EXTRATIME"

    def test_always_on(self):
        from kirby_cost.objects.modifiers import AlwaysOn
        mod = AlwaysOn()
        assert mod.XMLID == "ALWAYSON"


# ═══════════════════════════════════════════════════════════
#  ReducedEND — doubles value with Autofire
# ═══════════════════════════════════════════════════════════

class TestReducedEND:
    """ReducedEND.total_value doubles if parent has Autofire."""

    def test_basic_value(self):
        from kirby_cost.objects.modifiers import ReducedEND
        mod = ReducedEND()
        mod.base_cost = 0.25
        assert mod.total_value == 0.25

    def test_doubles_with_autofire(self):
        """When parent has Autofire, ReducedEND cost doubles."""
        from kirby_cost.objects.modifiers import ReducedEND
        mod = ReducedEND()
        mod.base_cost = 0.25

        parent = make_object(base_cost=50.0)
        autofire_mod = make_modifier(base_cost=0.5, xmlid="AUTOFIRE")
        parent.assigned_modifiers = [autofire_mod]
        mod.parent = parent

        assert mod.total_value == 0.5  # 0.25 * 2

    def test_no_double_without_autofire(self):
        from kirby_cost.objects.modifiers import ReducedEND
        mod = ReducedEND()
        mod.base_cost = 0.5

        parent = make_object(base_cost=50.0)
        parent.assigned_modifiers = []
        mod.parent = parent

        assert mod.total_value == 0.5

    def test_included_rejects_with_increased_end(self):
        """Cannot apply ReducedEND if power has IncreasedEND."""
        from kirby_cost.objects.modifiers import ReducedEND
        mod = ReducedEND()
        mod.base_cost = 0.25

        obj = make_object(base_cost=50.0)
        inc_end = make_modifier(base_cost=-0.25, xmlid="INCREASEDEND")
        obj.assigned_modifiers = [inc_end]

        result = mod.included(obj)
        assert "Increased END" in result

    def test_included_rejects_with_costs_end(self):
        from kirby_cost.objects.modifiers import ReducedEND
        mod = ReducedEND()
        mod.base_cost = 0.25

        obj = make_object(base_cost=50.0)
        costs_end = make_modifier(base_cost=-0.25, xmlid="COSTSEND")
        obj.assigned_modifiers = [costs_end]

        result = mod.included(obj)
        assert "Costs END" in result


# ═══════════════════════════════════════════════════════════
#  IncreasedEND — halves with CostsENDOnlyToActivate
# ═══════════════════════════════════════════════════════════

class TestIncreasedEND:
    """IncreasedEND.total_value halves if parent has CostsENDOnlyToActivate."""

    def test_basic_value(self):
        from kirby_cost.objects.modifiers import IncreasedEND
        mod = IncreasedEND()
        mod.base_cost = -0.25
        assert mod.total_value == -0.25

    def test_halves_with_costs_end_only_to_activate(self):
        from kirby_cost.objects.modifiers import IncreasedEND
        mod = IncreasedEND()
        mod.base_cost = -0.5

        parent = make_object(base_cost=50.0)
        ceota = make_modifier(base_cost=-0.25, xmlid="COSTSENDONLYTOACTIVATE")
        parent.assigned_modifiers = [ceota]
        mod.parent = parent
        mod._parent_object = parent  # progenitor

        assert mod.total_value == -0.25  # -0.5 / 2

    def test_included_rejects_with_reduced_end(self):
        from kirby_cost.objects.modifiers import IncreasedEND
        mod = IncreasedEND()
        mod.base_cost = -0.25

        obj = make_object(base_cost=50.0)
        red_end = make_modifier(base_cost=0.25, xmlid="REDUCEDEND")
        obj.assigned_modifiers = [red_end]

        result = mod.included(obj)
        assert "Reduced Endurance" in result


# ═══════════════════════════════════════════════════════════
#  SideEffects — cost adjustment for constant powers
# ═══════════════════════════════════════════════════════════

class TestSideEffects:
    """SideEffects.get_base_cost() adjusts for constant powers with activation."""

    def test_basic_value(self):
        from kirby_cost.objects.modifiers import SideEffects
        mod = SideEffects()
        mod.base_cost = -0.5
        assert mod.total_value == -0.5

    def test_constant_with_activation_roll(self):
        """Constant power with Activation Roll gets -0.25 discount."""
        from kirby_cost.objects.modifiers import SideEffects
        mod = SideEffects()
        mod.base_cost = -0.5

        parent = make_object(base_cost=50.0, duration="CONSTANT")
        act_roll = make_modifier(base_cost=-0.25, xmlid="ACTIVATIONROLL")
        parent.assigned_modifiers = [act_roll]
        mod.parent = parent

        # base_cost = -0.5 + (-0.25) = -0.75
        assert mod.base_cost == -0.75

    def test_instant_no_adjustment(self):
        """Instant power does NOT get the activation discount."""
        from kirby_cost.objects.modifiers import SideEffects
        mod = SideEffects()
        mod.base_cost = -0.5

        parent = make_object(base_cost=50.0, duration="INSTANT")
        act_roll = make_modifier(base_cost=-0.25, xmlid="ACTIVATIONROLL")
        parent.assigned_modifiers = [act_roll]
        mod.parent = parent

        assert mod.base_cost == -0.5  # No adjustment

    def test_constant_without_activation_no_adjustment(self):
        """Constant power WITHOUT activation roll gets no discount."""
        from kirby_cost.objects.modifiers import SideEffects
        mod = SideEffects()
        mod.base_cost = -0.5

        parent = make_object(base_cost=50.0, duration="CONSTANT")
        parent.assigned_modifiers = []
        mod.parent = parent

        assert mod.base_cost == -0.5


# ═══════════════════════════════════════════════════════════
#  Autofire — surcharge detection
# ═══════════════════════════════════════════════════════════

class TestAutofire:
    """Autofire has complex surcharge logic."""

    def test_basic_instantiation(self):
        from kirby_cost.objects.modifiers import Autofire
        mod = Autofire()
        assert mod.XMLID == "AUTOFIRE"
        assert mod.surcharge is False

    def test_basic_value_no_parent(self):
        from kirby_cost.objects.modifiers import Autofire
        mod = Autofire()
        mod.base_cost = 0.5
        # No parent, no surcharge
        assert mod.total_value == 0.5

    def test_included_rejects_self_only(self):
        """Autofire requires Attack Roll target."""
        from kirby_cost.objects.modifiers import Autofire
        mod = Autofire()
        obj = make_object(base_cost=50.0)
        obj.target = "SELFONLY"
        result = mod.included(obj)
        assert "Attack Roll" in result

    def test_included_allows_dcv_target(self):
        from kirby_cost.objects.modifiers import Autofire
        mod = Autofire()
        obj = make_object(base_cost=50.0)
        obj.target = "DCV"
        result = mod.included(obj)
        assert result == ""


# ═══════════════════════════════════════════════════════════
#  Integration: modifiers affecting power costs
# ═══════════════════════════════════════════════════════════

class TestModifierIntegrationCosts:
    """Test that specific modifier subclasses correctly affect power costs."""

    def test_focus_oif_reduces_cost(self):
        """OIF (-1/2) on 50pt power = 50 / 1.5 = 33."""
        from kirby_cost.objects.modifiers import Focus
        mod = Focus()
        mod.base_cost = -0.5

        obj = make_object(base_cost=50.0)
        obj.assigned_modifiers = [mod]

        assert obj.active_cost == 50.0  # Limitations don't affect active
        assert obj.real_cost_pre_list == 33.0

    def test_hardened_as_advantage(self):
        """Hardened (+1/4) on 30pt defense = 30 * 1.25 = 37.5 -> 37."""
        from kirby_cost.objects.modifiers import Hardened
        mod = Hardened()
        mod.base_cost = 0.25

        obj = make_object(base_cost=30.0)
        obj.assigned_modifiers = [mod]

        assert obj.active_cost == 37.0

    def test_reduced_end_as_advantage(self):
        """Reduced END (+1/4) on 40pt power = 40 * 1.25 = 50."""
        from kirby_cost.objects.modifiers import ReducedEND
        mod = ReducedEND()
        mod.base_cost = 0.25

        obj = make_object(base_cost=40.0)
        obj.assigned_modifiers = [mod]

        assert obj.active_cost == 50.0

    def test_mixed_specific_modifiers(self):
        """
        10d6 EB with Area Effect (+1/2), OIF (-1/2).
        Total = 50
        Active = 50 * 1.5 = 75
        Real = 75 / 1.5 = 50
        """
        from kirby_cost.objects.modifiers import AreaEffect, Focus
        aoe = AreaEffect()
        aoe.base_cost = 0.5
        oif = Focus()
        oif.base_cost = -0.5

        obj = make_object(
            base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0,
            xmlid="ENERGYBLAST"
        )
        obj.assigned_modifiers = [aoe, oif]

        assert obj.total_cost == 50.0
        assert obj.active_cost == 75.0
        assert obj.real_cost_pre_list == 50.0

    def test_gestures_incantations_focus(self):
        """
        30pt power with Gestures(-1/4), Incantations(-1/4), OAF(-1).
        Real = 30 / (1 + 1.5) = 30 / 2.5 = 12.
        """
        from kirby_cost.objects.modifiers import Gestures, Incantations, Focus
        gest = Gestures()
        gest.base_cost = -0.25
        inc = Incantations()
        inc.base_cost = -0.25
        oaf = Focus()
        oaf.base_cost = -1.0

        obj = make_object(base_cost=30.0)
        obj.assigned_modifiers = [gest, inc, oaf]

        assert obj.real_cost_pre_list == 12.0
