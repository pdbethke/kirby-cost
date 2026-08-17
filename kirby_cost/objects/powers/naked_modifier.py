"""
Naked Modifier power class for kirby-cost.

Converted from com.hero.objects.powers.NakedModifier.java

A Naked Modifier applies advantages/limitations to an existing ability
without buying the base power. Cost = levels * (non-private advantages).
"""

import math
from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_down
from kirby_cost.objects.frameworks import is_multipower, is_elemental_control
from kirby_cost.objects.modifiers.linked import is_linked


class NakedModifier(Power, xmlid="NAKEDMODIFIER"):
    """
    Naked Modifier power.

    Cost is based on the Active Points of the ability being modified,
    multiplied by the non-private modifier advantages.
    """

    def __init__(self):
        super().__init__()
        self.xmlid = NakedModifier.XMLID
        self._duration = "CONSTANT"

    @property
    def damage_display(self) -> str:
        return ""

    @property
    def naked_real_cost(self) -> float:
        """
        Calculate the naked real cost.

        This is: levels * (1 + non-private advantages) - levels
        i.e., just the cost of the advantages on the given number of active points.

        Ported from NakedModifier.java getNakedRealCost().
        """
        d = 0.0
        adv_total = 0.0

        for modifier in self.assigned_modifiers:
            if modifier.private:
                continue
            val = modifier.total_value
            if val > 0.0:
                adv_total += val

        if adv_total > 0.0:
            d = round_half_down(float(self._levels) * (1.0 + adv_total) - float(self._levels))

        return d

    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""


        return self._compute_active_cost()



    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """
        Calculate active cost for Naked Modifier.

        Start with naked real cost, then apply private (framework-level) advantages.

        Ported from NakedModifier.java getActiveCost().
        """
        d = self.naked_real_cost

        # Sum private advantages from own modifiers
        private_adv_total = 0.0
        has_private_adv = False
        for modifier in self.assigned_modifiers:
            if not modifier.private:
                continue
            if modifier.total_value > 0.0:
                private_adv_total += modifier.total_value
                has_private_adv = True

        # Sum advantages from parent list
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent

        if parent:
            for modifier in parent.assigned_modifiers:
                if modifier.types and "VPP" in modifier.types:
                    continue
                if modifier.xmlid == "CHARGES" and is_multipower(parent):
                    continue
                if is_linked(modifier):
                    continue
                if modifier.total_value <= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, modifier.xmlid) and
                    modifier.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                if is_multipower(parent) or is_elemental_control(parent):
                    continue
                private_adv_total += modifier.total_value
                has_private_adv = True

        if has_private_adv:
            d = round_half_down(d * (1.0 + private_adv_total))

        return d

    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost for Naked Modifier.

        Apply private limitations to active cost.

        Ported from NakedModifier.java getRealCostPreList().
        """
        d = self.active_cost

        private_lim_total = 0.0
        has_naked_adv = False
        has_naked_lim = False

        for modifier in self.assigned_modifiers:
            if not modifier.private:
                if modifier.total_value > 0.0:
                    has_naked_adv = True
                elif modifier.total_value < 0.0:
                    has_naked_lim = True
            if modifier.private and modifier.total_value < 0.0:
                private_lim_total += modifier.total_value

        # Parent list limitations
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent

        if parent:
            for modifier in parent.assigned_modifiers:
                if modifier.types and "VPP" in modifier.types:
                    continue
                if modifier.xmlid == "CHARGES" and is_multipower(self._parent):
                    continue
                if modifier.total_value >= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, modifier.xmlid) and
                    modifier.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                private_lim_total += modifier.total_value

        if private_lim_total != 0.0:
            d = round_half_down(d / (1.0 + abs(private_lim_total)))

        # Multiplier
        if self.multiplier != 1.0:
            d *= self.multiplier
            d = round_half_down(d)

        # Minimum 1 CP if has advantages but no limitations
        if has_naked_adv and not has_naked_lim and d < 1.0:
            d = 1.0

        # Quantity cost
        if self._quantity > 1:
            qty_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                qty_cost += 5
                qty /= 2.0
            d += float(qty_cost)

        return d
