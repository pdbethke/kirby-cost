"""
Tests for kirby_cost.objects.base.GenericObject

Verifies the core cost calculation engine:
  get_total_cost()    — base + levels + adders
  get_active_cost()   — total * (1 + advantages)
  get_real_cost_pre_list() — active / (1 + |limitations|)

Reference: HD6_SOURCE_CODE_FORMULAS.md - sections 1-3.
All expected values verified against the Java source formulas.
"""

import pytest
from tests.conftest import make_object, make_modifier, make_adder, ConcreteObject


# ═══════════════════════════════════════════════════════════
#  get_total_cost()
# ═══════════════════════════════════════════════════════════

class TestTotalCostBasic:
    """Total cost with no levels or adders is just base cost."""

    def test_base_cost_only(self):
        obj = make_object(base_cost=10.0)
        assert obj.total_cost == 10.0

    def test_zero_cost(self):
        obj = make_object(base_cost=0.0)
        assert obj.total_cost == 0.0

    def test_negative_base_cost(self):
        obj = make_object(base_cost=-5.0)
        assert obj.total_cost == -5.0


class TestTotalCostWithLevels:
    """Level cost: floor(levels / level_value) * level_cost."""

    def test_simple_levels(self):
        """10d6 Energy Blast: base=0, 10 levels at 5pts each = 50."""
        obj = make_object(base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0)
        assert obj.total_cost == 50.0

    def test_levels_with_base(self):
        """Base 3 + 5 levels at 2pts = 3 + 10 = 13."""
        obj = make_object(base_cost=3.0, levels=5, level_value=1.0, level_cost=2.0)
        assert obj.total_cost == 13.0

    def test_fractional_level_value(self):
        """level_value=2.0: 4 levels / 2.0 = 2 increments * level_cost."""
        obj = make_object(base_cost=0.0, levels=4, level_value=2.0, level_cost=5.0)
        assert obj.total_cost == 10.0

    def test_partial_levels_round_up(self):
        """3 levels / 2.0 = 1.5, floor=1, but partial -> +1 = 2 increments."""
        obj = make_object(base_cost=0.0, levels=3, level_value=2.0, level_cost=5.0)
        assert obj.total_cost == 10.0  # 2 * 5

    def test_single_level(self):
        """1 level at 5pts."""
        obj = make_object(base_cost=0.0, levels=1, level_value=1.0, level_cost=5.0)
        assert obj.total_cost == 5.0

    def test_zero_levels(self):
        """0 levels should add nothing."""
        obj = make_object(base_cost=5.0, levels=0, level_value=1.0, level_cost=3.0)
        assert obj.total_cost == 5.0

    def test_fractional_level_cost_rounding(self):
        """When level_cost < level_value, result is rounded."""
        obj = make_object(base_cost=0.0, levels=3, level_value=1.0, level_cost=0.5)
        # 3 * 0.5 = 1.5, level_cost(0.5) < level_value(1.0) so round: 1.5 -> round_half_down -> 1
        # But 1.5 rounds to 1 (half down)? Actually 0 + 1.5 = 1.5 -> round_half_down(1.5) = 1
        assert obj.total_cost == 1.0


class TestTotalCostWithAdders:
    """Adder costs are added to total in priority order."""

    def test_required_adder(self):
        obj = make_object(base_cost=10.0)
        adder = make_adder(base_cost=5.0, required=True, xmlid="REQ_ADDER")
        obj.assigned_adders = [adder]
        assert obj.total_cost == 15.0

    def test_available_adder(self):
        """Non-required adder that's in the available list."""
        obj = make_object(base_cost=10.0)
        adder = make_adder(base_cost=3.0, required=False, xmlid="OPT_ADDER")
        available = make_adder(base_cost=0.0, xmlid="OPT_ADDER")
        obj.assigned_adders = [adder]
        obj.available_adders = [available]
        assert obj.total_cost == 13.0

    def test_custom_adder_added_after_limits(self):
        """Adders not in available list are added after min/max limits."""
        obj = make_object(base_cost=10.0, minimum_cost=5.0, min_set=True)
        custom = make_adder(base_cost=7.0, required=False, xmlid="CUSTOM")
        obj.assigned_adders = [custom]
        # base=10, no available match -> treated as custom adder
        # min/max applied to 10 (still 10 since 10 > 5)
        # then custom added: 10 + 7 = 17
        assert obj.total_cost == 17.0

    def test_multiple_adders(self):
        obj = make_object(base_cost=5.0)
        a1 = make_adder(base_cost=2.0, required=True, xmlid="A1")
        a2 = make_adder(base_cost=3.0, required=True, xmlid="A2")
        obj.assigned_adders = [a1, a2]
        assert obj.total_cost == 10.0


class TestTotalCostMinMax:
    """Minimum and maximum cost limits."""

    def test_minimum_enforced(self):
        obj = make_object(base_cost=0.5, minimum_cost=1.0, min_set=True)
        assert obj.total_cost == 1.0

    def test_maximum_enforced(self):
        obj = make_object(base_cost=100.0, max_cost=50.0, max_set=True)
        assert obj.total_cost == 50.0

    def test_min_not_set_ignored(self):
        obj = make_object(base_cost=0.5, minimum_cost=1.0, min_set=False)
        assert obj.total_cost == 0.5

    def test_max_not_set_ignored(self):
        obj = make_object(base_cost=100.0, max_cost=50.0, max_set=False)
        assert obj.total_cost == 100.0


# ═══════════════════════════════════════════════════════════
#  get_active_cost()
# ═══════════════════════════════════════════════════════════

class TestActiveCostNoModifiers:
    """Without modifiers, active cost equals total cost."""

    def test_no_modifiers(self):
        obj = make_object(base_cost=50.0)
        assert obj.active_cost == 50.0

    def test_levels_no_modifiers(self):
        obj = make_object(base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0)
        assert obj.active_cost == 50.0


class TestActiveCostWithAdvantages:
    """Active Cost = Total Cost * (1 + sum_of_advantages)."""

    def test_single_half_advantage(self):
        """50 * (1 + 0.5) = 75."""
        obj = make_object(base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0)
        mod = make_modifier(base_cost=0.5, xmlid="ADVANTAGE1")
        obj.assigned_modifiers = [mod]
        assert obj.active_cost == 75.0

    def test_single_full_advantage(self):
        """50 * (1 + 1.0) = 100."""
        obj = make_object(base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0)
        mod = make_modifier(base_cost=1.0, xmlid="ADVANTAGE1")
        obj.assigned_modifiers = [mod]
        assert obj.active_cost == 100.0

    def test_multiple_advantages(self):
        """50 * (1 + 0.5 + 0.25) = 50 * 1.75 = 87.5 -> round_half_down -> 87."""
        obj = make_object(base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0)
        m1 = make_modifier(base_cost=0.5, xmlid="ADV1")
        m2 = make_modifier(base_cost=0.25, xmlid="ADV2")
        obj.assigned_modifiers = [m1, m2]
        assert obj.active_cost == 87.0

    def test_advantage_with_rounding(self):
        """30 * 1.5 = 45 (no rounding needed)."""
        obj = make_object(base_cost=30.0)
        mod = make_modifier(base_cost=0.5, xmlid="ADV1")
        obj.assigned_modifiers = [mod]
        assert obj.active_cost == 45.0

    def test_advantage_rounds_half_down(self):
        """15 * (1 + 0.5) = 22.5 -> round_half_down -> 22."""
        obj = make_object(base_cost=15.0)
        mod = make_modifier(base_cost=0.5, xmlid="ADV1")
        obj.assigned_modifiers = [mod]
        assert obj.active_cost == 22.0

    def test_minimum_active_cost_one(self):
        """If total > 0 and active rounds to < 1, force 1."""
        obj = make_object(base_cost=1.0)
        # +0.25 advantage on 1pt: 1 * 1.25 = 1.25 -> round -> 1. Fine.
        # Need a case where rounding drops below 1.
        # With base=0.5 it stays 0.5 total cost which is > 0...
        # Actually with base_cost=0.1 the total is 0.1, active = 0.1 * 1.25 = 0.125 -> 0
        # But min active cost = 1 when total > 0
        obj2 = make_object(base_cost=0.1)
        mod = make_modifier(base_cost=0.25, xmlid="ADV")
        obj2.assigned_modifiers = [mod]
        assert obj2.active_cost == 1.0


class TestActiveCostIgnoresLimitations:
    """Negative modifiers (limitations) do NOT affect active cost."""

    def test_limitation_ignored(self):
        """50 with -0.5 limitation: active cost still 50."""
        obj = make_object(base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0)
        lim = make_modifier(base_cost=-0.5, xmlid="LIMITATION")
        obj.assigned_modifiers = [lim]
        assert obj.active_cost == 50.0

    def test_mixed_modifiers(self):
        """Only advantages contribute to active cost."""
        obj = make_object(base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0)
        adv = make_modifier(base_cost=0.5, xmlid="ADV")
        lim = make_modifier(base_cost=-0.25, xmlid="LIM")
        obj.assigned_modifiers = [adv, lim]
        # Active = 50 * (1 + 0.5) = 75 (limitation ignored)
        assert obj.active_cost == 75.0


# ═══════════════════════════════════════════════════════════
#  get_real_cost_pre_list()
# ═══════════════════════════════════════════════════════════

class TestRealCostNoModifiers:
    """Without modifiers, real cost equals active cost equals total cost."""

    def test_no_modifiers(self):
        obj = make_object(base_cost=50.0)
        assert obj.real_cost_pre_list == 50.0


class TestRealCostWithLimitations:
    """Real Cost = Active Cost / (1 + |limitations|)."""

    def test_quarter_limitation(self):
        """100 / (1 + 0.25) = 100 / 1.25 = 80."""
        obj = make_object(base_cost=0.0, levels=10, level_value=1.0, level_cost=5.0)
        adv = make_modifier(base_cost=1.0, xmlid="ADV")
        lim = make_modifier(base_cost=-0.25, xmlid="LIM")
        obj.assigned_modifiers = [adv, lim]
        # Active = 50 * (1 + 1.0) = 100
        # Real = 100 / (1 + 0.25) = 80
        assert obj.real_cost_pre_list == 80.0

    def test_half_limitation(self):
        """50 / (1 + 0.5) = 50 / 1.5 = 33.333 -> round_half_down -> 33."""
        obj = make_object(base_cost=50.0)
        lim = make_modifier(base_cost=-0.5, xmlid="LIM")
        obj.assigned_modifiers = [lim]
        assert obj.real_cost_pre_list == 33.0

    def test_full_limitation(self):
        """50 / (1 + 1.0) = 50 / 2.0 = 25."""
        obj = make_object(base_cost=50.0)
        lim = make_modifier(base_cost=-1.0, xmlid="LIM")
        obj.assigned_modifiers = [lim]
        assert obj.real_cost_pre_list == 25.0

    def test_two_limitations(self):
        """50 / (1 + 0.5 + 0.25) = 50 / 1.75 = 28.571 -> 29."""
        obj = make_object(base_cost=50.0)
        l1 = make_modifier(base_cost=-0.5, xmlid="L1")
        l2 = make_modifier(base_cost=-0.25, xmlid="L2")
        obj.assigned_modifiers = [l1, l2]
        assert obj.real_cost_pre_list == 29.0

    def test_heavy_limitation(self):
        """50 / (1 + 2.0) = 50 / 3.0 = 16.666 -> 17."""
        obj = make_object(base_cost=50.0)
        lim = make_modifier(base_cost=-2.0, xmlid="LIM")
        obj.assigned_modifiers = [lim]
        assert obj.real_cost_pre_list == 17.0


class TestRealCostMinimumOne:
    """Most objects have a minimum real cost of 1 point."""

    def test_minimum_one_point(self):
        """Small power with heavy limitation shouldn't go below 1."""
        obj = make_object(base_cost=5.0)
        lim = make_modifier(base_cost=-10.0, xmlid="LIM", min_set=False)
        obj.assigned_modifiers = [lim]
        # 5 / (1 + 10) = 5 / 11 = 0.45 -> round -> 0, but minimum 1
        assert obj.real_cost_pre_list == 1.0


class TestCompleteCalculationChain:
    """
    Full calculation chain examples from HD6_SOURCE_CODE_FORMULAS.md.
    These verify the entire pipeline: total -> active -> real.
    """

    def test_energy_blast_10d6_with_advantage_and_limitation(self):
        """
        10d6 Energy Blast with +1 Advantage and -1/4 Limitation.
        Total = 0 + 10*5 = 50
        Active = 50 * (1 + 1) = 100
        Real = 100 / (1 + 0.25) = 80
        """
        obj = make_object(
            base_cost=0.0,
            levels=10,
            level_value=1.0,
            level_cost=5.0,
            xmlid="ENERGYBLAST",
        )
        adv = make_modifier(base_cost=1.0, xmlid="ADV")
        lim = make_modifier(base_cost=-0.25, xmlid="LIM")
        obj.assigned_modifiers = [adv, lim]

        assert obj.total_cost == 50.0
        assert obj.active_cost == 100.0
        assert obj.real_cost_pre_list == 80.0

    def test_flight_12m_no_modifiers(self):
        """
        Flight 12m: base=0, 12 levels at 1pt each = 12.
        No modifiers: active=12, real=12.
        """
        obj = make_object(
            base_cost=0.0,
            levels=12,
            level_value=1.0,
            level_cost=1.0,
            xmlid="FLIGHT",
        )
        assert obj.total_cost == 12.0
        assert obj.active_cost == 12.0
        assert obj.real_cost_pre_list == 12.0

    def test_armor_10pd_10ed(self):
        """
        Resistant Protection 10 PD / 10 ED: base=0, levels=10, cost=3/level.
        Total = 30. No mods. Real = 30.
        """
        obj = make_object(
            base_cost=0.0,
            levels=10,
            level_value=1.0,
            level_cost=3.0,
            xmlid="ARMOR",
        )
        assert obj.total_cost == 30.0
        assert obj.real_cost_pre_list == 30.0

    def test_power_with_two_advantages_one_limitation(self):
        """
        40-point power with +1/2 and +1/4 advantages, -1/2 limitation.
        Active = 40 * (1 + 0.5 + 0.25) = 40 * 1.75 = 70
        Real = 70 / (1 + 0.5) = 70 / 1.5 = 46.666 -> 47
        """
        obj = make_object(base_cost=40.0)
        a1 = make_modifier(base_cost=0.5, xmlid="ADV1")
        a2 = make_modifier(base_cost=0.25, xmlid="ADV2")
        lim = make_modifier(base_cost=-0.5, xmlid="LIM")
        obj.assigned_modifiers = [a1, a2, lim]

        assert obj.total_cost == 40.0
        assert obj.active_cost == 70.0
        assert obj.real_cost_pre_list == 47.0

    def test_power_with_heavy_modifiers(self):
        """
        60-point power with +2 advantage, -1 and -1/2 limitations.
        Active = 60 * (1 + 2) = 180
        Real = 180 / (1 + 1.5) = 180 / 2.5 = 72
        """
        obj = make_object(base_cost=60.0)
        adv = make_modifier(base_cost=2.0, xmlid="ADV")
        l1 = make_modifier(base_cost=-1.0, xmlid="L1")
        l2 = make_modifier(base_cost=-0.5, xmlid="L2")
        obj.assigned_modifiers = [adv, l1, l2]

        assert obj.total_cost == 60.0
        assert obj.active_cost == 180.0
        assert obj.real_cost_pre_list == 72.0


# ═══════════════════════════════════════════════════════════
#  Utility / lookup methods
# ═══════════════════════════════════════════════════════════

class TestFindObjectById:
    """find_object_by_id: searches a list for matching XMLID."""

    def test_find_existing(self):
        obj1 = make_object(xmlid="ALPHA")
        obj2 = make_object(xmlid="BETA")
        found = ConcreteObject.find_object_by_id([obj1, obj2], "BETA")
        assert found is obj2

    def test_case_insensitive(self):
        obj = make_object(xmlid="ENERGYBLAST")
        found = ConcreteObject.find_object_by_id([obj], "energyblast")
        assert found is obj

    def test_not_found(self):
        obj = make_object(xmlid="ALPHA")
        found = ConcreteObject.find_object_by_id([obj], "MISSING")
        assert found is None

    def test_empty_list(self):
        found = ConcreteObject.find_object_by_id([], "ANYTHING")
        assert found is None

    def test_none_list(self):
        found = ConcreteObject.find_object_by_id(None, "ANYTHING")
        assert found is None


class TestFindModifierById:
    """find_modifier_by_id: convenience method on GenericObject."""

    def test_find_assigned_modifier(self):
        obj = make_object()
        mod = make_modifier(xmlid="RANGED")
        obj.assigned_modifiers = [mod]
        assert obj.find_modifier_by_id("RANGED") is mod

    def test_not_found(self):
        obj = make_object()
        assert obj.find_modifier_by_id("MISSING") is None


class TestXmlidTranslation:
    """XMLID translations for backward compatibility.

    Translation now happens at XML parse time (_init), not at read time.
    Direct assignment preserves the raw value.
    """

    def test_radio_transmission_translation(self):
        """Translation applied during XML loading, not direct assignment."""
        obj = make_object(xmlid="RADIOTRANSMISSION")
        # Direct assignment keeps raw value; translation only in _init
        assert obj.xmlid == "RADIOTRANSMISSION"

    def test_ir_perception_translation(self):
        obj = make_object(xmlid="IRPERCEPTION")
        assert obj.xmlid == "IRPERCEPTION"

    def test_no_translation_needed(self):
        obj = make_object(xmlid="ENERGYBLAST")
        assert obj.xmlid == "ENERGYBLAST"

    def test_none_xmlid(self):
        obj = make_object()
        obj.xmlid = None
        assert obj.xmlid is None


# ═══════════════════════════════════════════════════════════
#  Identity — the id is what consumers index on
# ═══════════════════════════════════════════════════════════

class TestObjectIdentity:
    """The id IS the object's identity, so it must not move under anyone.

    Kirby indexes on ids and never on xmlid or name: the xmlid is a TYPE, and
    a character may carry several powers agreeing on both xmlid and name. An
    identity that a caller can reassign is no identity at all — a stale handle
    would then point at a different object instead of failing loudly.
    """

    def test_id_is_read_only(self):
        obj = make_object(xmlid="ENERGYBLAST")
        with pytest.raises(AttributeError):
            obj.id = 999

    def test_id_survives_a_failed_assignment(self):
        obj = make_object(xmlid="ENERGYBLAST")
        before = obj.id
        with pytest.raises(AttributeError):
            obj.id = 999
        assert obj.id == before

    def test_two_objects_never_share_an_id(self):
        a = make_object(xmlid="ENERGYBLAST")
        b = make_object(xmlid="ENERGYBLAST")
        assert a.id != b.id
