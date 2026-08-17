"""
Integration tests for the complete cost calculation chain.

These tests validate the full pipeline:
  Total Cost → Active Cost → Real Cost

using realistic Champions 6E character builds. Expected values are derived
from the formulas in HD6_SOURCE_CODE_FORMULAS.md and cross-checked against
the actual Hero Designer 6 application.

Each test documents the build so results can be verified by hand.
"""

import pytest
from tests.conftest import make_object, make_modifier, make_adder


# ═══════════════════════════════════════════════════════════
#  Attack Powers
# ═══════════════════════════════════════════════════════════

class TestEnergyBlastCalculations:
    """Energy Blast: base=0, level_cost=5 per d6."""

    def test_8d6_no_modifiers(self):
        """8d6 EB = 40 pts. No mods."""
        obj = make_object(levels=8, level_value=1.0, level_cost=5.0, xmlid="ENERGYBLAST")
        assert obj.total_cost == 40.0
        assert obj.active_cost == 40.0
        assert obj.real_cost_pre_list == 40.0

    def test_12d6_with_area_effect(self):
        """
        12d6 EB, Area Effect (+1/2).
        Total = 60, Active = 60 * 1.5 = 90, Real = 90.
        """
        obj = make_object(levels=12, level_value=1.0, level_cost=5.0, xmlid="ENERGYBLAST")
        aoe = make_modifier(base_cost=0.5, xmlid="AOE")
        obj.assigned_modifiers = [aoe]
        assert obj.total_cost == 60.0
        assert obj.active_cost == 90.0
        assert obj.real_cost_pre_list == 90.0

    def test_10d6_ranged_oif(self):
        """
        10d6 EB, Ranged (+1/2), OIF (-1/2).
        Wait — EB is already ranged by default. Let's use a different advantage.

        10d6 EB, Armor Piercing (+1/4), OIF (-1/2).
        Total = 50
        Active = 50 * (1 + 0.25) = 62.5 -> round_half_down -> 62
        Real = 62 / (1 + 0.5) = 41.333 -> round_half_down -> 41
        """
        obj = make_object(levels=10, level_value=1.0, level_cost=5.0, xmlid="ENERGYBLAST")
        ap = make_modifier(base_cost=0.25, xmlid="ARMORPIERCING")
        oif = make_modifier(base_cost=-0.5, xmlid="FOCUS")
        obj.assigned_modifiers = [ap, oif]

        assert obj.total_cost == 50.0
        assert obj.active_cost == 62.0
        assert obj.real_cost_pre_list == 41.0

    def test_6d6_heavy_limitations(self):
        """
        6d6 EB with OAF(-1), Gestures(-1/4), Incantations(-1/4).
        Total = 30
        Active = 30 (no advantages)
        Real = 30 / (1 + 1.5) = 30 / 2.5 = 12
        """
        obj = make_object(levels=6, level_value=1.0, level_cost=5.0, xmlid="ENERGYBLAST")
        oaf = make_modifier(base_cost=-1.0, xmlid="FOCUS")
        gest = make_modifier(base_cost=-0.25, xmlid="GESTURES")
        inc = make_modifier(base_cost=-0.25, xmlid="INCANTATIONS")
        obj.assigned_modifiers = [oaf, gest, inc]

        assert obj.total_cost == 30.0
        assert obj.active_cost == 30.0
        assert obj.real_cost_pre_list == 12.0


class TestKillingAttackCalculations:
    """Killing Attack (Ranged): base=0, level_cost=15 per d6."""

    def test_2d6_rka(self):
        """2d6 RKA = 30 pts."""
        obj = make_object(levels=2, level_value=1.0, level_cost=15.0, xmlid="KILLINGATTACK")
        assert obj.total_cost == 30.0

    def test_3d6_rka_with_advantage_and_limitation(self):
        """
        3d6 RKA, AP (+1/4), OIF (-1/2).
        Total = 45
        Active = 45 * 1.25 = 56.25 -> 56
        Real = 56 / 1.5 = 37.333 -> 37
        """
        obj = make_object(levels=3, level_value=1.0, level_cost=15.0, xmlid="KILLINGATTACK")
        ap = make_modifier(base_cost=0.25, xmlid="ARMORPIERCING")
        oif = make_modifier(base_cost=-0.5, xmlid="FOCUS")
        obj.assigned_modifiers = [ap, oif]

        assert obj.total_cost == 45.0
        assert obj.active_cost == 56.0
        assert obj.real_cost_pre_list == 37.0


# ═══════════════════════════════════════════════════════════
#  Defense Powers
# ═══════════════════════════════════════════════════════════

class TestArmorCalculations:
    """Resistant Protection: base=0, level_cost=3 (combined PD+ED per level)."""

    def test_15_rpd_red(self):
        """15 rPD/rED = 15 * 3 = 45 pts."""
        obj = make_object(levels=15, level_value=1.0, level_cost=3.0, xmlid="ARMOR")
        assert obj.total_cost == 45.0

    def test_10_armor_half_limitation(self):
        """
        10 Armor, Focus (-1/2).
        Total = 30, Active = 30, Real = 30/1.5 = 20.
        """
        obj = make_object(levels=10, level_value=1.0, level_cost=3.0, xmlid="ARMOR")
        focus = make_modifier(base_cost=-0.5, xmlid="FOCUS")
        obj.assigned_modifiers = [focus]
        assert obj.real_cost_pre_list == 20.0


class TestForceFieldCalculations:
    """Force Field: base=0, level_cost=1 per point of defense."""

    def test_20pd_20ed(self):
        """20 PD + 20 ED Force Field, base=0, 20 levels at 2pts each = 40."""
        obj = make_object(levels=20, level_value=1.0, level_cost=2.0, xmlid="FORCEFIELD")
        assert obj.total_cost == 40.0


# ═══════════════════════════════════════════════════════════
#  Movement Powers
# ═══════════════════════════════════════════════════════════

class TestFlightCalculations:
    """Flight: base=0, level_cost=1 per meter."""

    def test_30m_flight(self):
        """30m Flight = 30 pts."""
        obj = make_object(levels=30, level_value=1.0, level_cost=1.0, xmlid="FLIGHT")
        assert obj.total_cost == 30.0
        assert obj.real_cost_pre_list == 30.0

    def test_40m_flight_oif(self):
        """
        40m Flight, OIF (-1/2).
        Total = 40, Active = 40, Real = 40/1.5 = 26.666 -> 27.
        """
        obj = make_object(levels=40, level_value=1.0, level_cost=1.0, xmlid="FLIGHT")
        oif = make_modifier(base_cost=-0.5, xmlid="FOCUS")
        obj.assigned_modifiers = [oif]
        assert obj.real_cost_pre_list == 27.0


class TestTeleportationCalculations:
    """Teleportation: base=0, level_cost=1 per meter."""

    def test_20m_teleport_oaf(self):
        """
        20m Teleport, OAF (-1).
        Total = 20, Active = 20, Real = 20/2 = 10.
        """
        obj = make_object(levels=20, level_value=1.0, level_cost=1.0, xmlid="TELEPORTATION")
        oaf = make_modifier(base_cost=-1.0, xmlid="FOCUS")
        obj.assigned_modifiers = [oaf]
        assert obj.real_cost_pre_list == 10.0


# ═══════════════════════════════════════════════════════════
#  Complex modifier scenarios
# ═══════════════════════════════════════════════════════════

class TestComplexModifierScenarios:
    """Tests with multiple advantages and limitations in realistic combinations."""

    def test_fully_loaded_attack(self):
        """
        10d6 EB with:
          Armor Piercing (+1/4)
          Area Effect (+1/2)
          Reduced END (+1/2)
          OAF (-1)
          Gestures (-1/4)

        Total = 50
        Advantages = 0.25 + 0.5 + 0.5 = 1.25
        Active = 50 * (1 + 1.25) = 50 * 2.25 = 112.5 -> 112
        Limitations = 1.0 + 0.25 = 1.25
        Real = 112 / (1 + 1.25) = 112 / 2.25 = 49.777 -> 50
        """
        obj = make_object(levels=10, level_value=1.0, level_cost=5.0, xmlid="ENERGYBLAST")
        m_ap = make_modifier(base_cost=0.25, xmlid="ARMORPIERCING")
        m_aoe = make_modifier(base_cost=0.5, xmlid="AOE")
        m_rend = make_modifier(base_cost=0.5, xmlid="REDUCEDEND")
        m_oaf = make_modifier(base_cost=-1.0, xmlid="FOCUS")
        m_gest = make_modifier(base_cost=-0.25, xmlid="GESTURES")
        obj.assigned_modifiers = [m_ap, m_aoe, m_rend, m_oaf, m_gest]

        assert obj.total_cost == 50.0
        assert obj.active_cost == 112.0
        assert obj.real_cost_pre_list == 50.0

    def test_advantages_only(self):
        """
        20-point base with +3/4 and +1/2 advantages, no limitations.
        Active = 20 * (1 + 0.75 + 0.5) = 20 * 2.25 = 45
        Real = 45 (no limitations)
        """
        obj = make_object(base_cost=20.0)
        a1 = make_modifier(base_cost=0.75, xmlid="ADV1")
        a2 = make_modifier(base_cost=0.5, xmlid="ADV2")
        obj.assigned_modifiers = [a1, a2]

        assert obj.active_cost == 45.0
        assert obj.real_cost_pre_list == 45.0

    def test_limitations_only(self):
        """
        50-point base with -1 and -1/2 limitations, no advantages.
        Active = 50
        Real = 50 / (1 + 1.5) = 50 / 2.5 = 20
        """
        obj = make_object(base_cost=50.0)
        l1 = make_modifier(base_cost=-1.0, xmlid="L1")
        l2 = make_modifier(base_cost=-0.5, xmlid="L2")
        obj.assigned_modifiers = [l1, l2]

        assert obj.active_cost == 50.0
        assert obj.real_cost_pre_list == 20.0

    def test_adder_with_modifier(self):
        """
        Power with adder affecting base, then modified.
        Base=10, required adder=5 -> total=15
        +1/2 advantage: active = 15 * 1.5 = 22.5 -> 22
        -1/4 limitation: real = 22 / 1.25 = 17.6 -> 18
        """
        obj = make_object(base_cost=10.0)
        adder = make_adder(base_cost=5.0, required=True, xmlid="REQ")
        adv = make_modifier(base_cost=0.5, xmlid="ADV")
        lim = make_modifier(base_cost=-0.25, xmlid="LIM")
        obj.assigned_adders = [adder]
        obj.assigned_modifiers = [adv, lim]

        assert obj.total_cost == 15.0
        assert obj.active_cost == 22.0
        assert obj.real_cost_pre_list == 18.0


# ═══════════════════════════════════════════════════════════
#  Edge cases and rounding boundaries
# ═══════════════════════════════════════════════════════════

class TestRoundingEdgeCases:
    """
    Tests targeting rounding boundaries where half-down vs half-up matters.
    These are the calculations most likely to differ from naive implementations.
    """

    def test_exact_half_in_active_cost(self):
        """
        Total=15, +1/2 advantage.
        Active = 15 * 1.5 = 22.5 -> round_half_down -> 22
        """
        obj = make_object(base_cost=15.0)
        adv = make_modifier(base_cost=0.5, xmlid="ADV")
        obj.assigned_modifiers = [adv]
        assert obj.active_cost == 22.0

    def test_exact_half_in_real_cost(self):
        """
        Active=25, -1/2 limitation.
        Real = 25 / 1.5 = 16.666... -> round_half_down -> 17
        """
        obj = make_object(base_cost=25.0)
        lim = make_modifier(base_cost=-0.5, xmlid="LIM")
        obj.assigned_modifiers = [lim]
        assert obj.real_cost_pre_list == 17.0

    def test_active_cost_rounds_down_at_half(self):
        """
        Total=5, +1/2 advantage.
        Active = 5 * 1.5 = 7.5 -> round_half_down -> 7
        """
        obj = make_object(base_cost=5.0)
        adv = make_modifier(base_cost=0.5, xmlid="ADV")
        obj.assigned_modifiers = [adv]
        assert obj.active_cost == 7.0

    def test_one_third_values(self):
        """
        60 / (1 + 2.0) = 60 / 3 = 20.0 (exact).
        """
        obj = make_object(base_cost=60.0)
        lim = make_modifier(base_cost=-2.0, xmlid="LIM")
        obj.assigned_modifiers = [lim]
        assert obj.real_cost_pre_list == 20.0

    def test_repeating_decimal(self):
        """
        70 / (1 + 0.5) = 70 / 1.5 = 46.666... -> 47
        """
        obj = make_object(base_cost=70.0)
        lim = make_modifier(base_cost=-0.5, xmlid="LIM")
        obj.assigned_modifiers = [lim]
        assert obj.real_cost_pre_list == 47.0

    def test_large_power_with_many_modifiers(self):
        """
        80 base, +2 advantage, -1 and -1/4 limitations.
        Active = 80 * (1 + 2) = 240
        Real = 240 / (1 + 1.25) = 240 / 2.25 = 106.666... -> 107
        """
        obj = make_object(base_cost=80.0)
        adv = make_modifier(base_cost=2.0, xmlid="ADV")
        l1 = make_modifier(base_cost=-1.0, xmlid="L1")
        l2 = make_modifier(base_cost=-0.25, xmlid="L2")
        obj.assigned_modifiers = [adv, l1, l2]

        assert obj.active_cost == 240.0
        assert obj.real_cost_pre_list == 107.0


# ═══════════════════════════════════════════════════════════
#  Quantity multiplier
# ═══════════════════════════════════════════════════════════

class TestQuantityMultiplier:
    """Quantity > 1 adds 5 points per doubling."""

    def test_quantity_one_no_effect(self):
        obj = make_object(base_cost=10.0)
        obj.quantity = 1
        assert obj.real_cost_pre_list == 10.0

    def test_quantity_two(self):
        """2 copies: +5 points."""
        obj = make_object(base_cost=10.0)
        obj.quantity = 2
        assert obj.real_cost_pre_list == 15.0

    def test_quantity_four(self):
        """4 copies: +10 points (two doublings)."""
        obj = make_object(base_cost=10.0)
        obj.quantity = 4
        assert obj.real_cost_pre_list == 20.0

    def test_quantity_eight(self):
        """8 copies: +15 points (three doublings)."""
        obj = make_object(base_cost=10.0)
        obj.quantity = 8
        assert obj.real_cost_pre_list == 25.0
