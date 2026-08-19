"""
Naked Modifier power class for kirby-cost.

Converted from com.hero.objects.powers.NakedModifier.java

A Naked Modifier applies advantages/limitations to an existing ability
without buying the base power. Cost = levels * (non-private advantages).
"""

import math
from kirby_cost.objects.base import GenericObject, _show_common_limitations
from kirby_cost.util.rounder import round_up
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

    def _naked_modifier_string(self) -> str:
        """The modifiers this power SELLS, which is the whole of what it is.

        Ported from ``NakedModifier.getNakedModifierString``. A Naked Advantage
        is not a power with modifiers attached — it IS the modifier, bought
        separately and applied to something else, so its own modifiers are its
        subject rather than its decoration. Private modifiers are dropped
        (they belong to `modifier_string`, which prints only those), and
        advantages come before limitations with the usual "; " between the
        groups.
        """
        mods = [m for m in self._assigned_modifiers if not m.private]
        mods.sort(key=lambda m: m.total_value)
        ret = ""
        for m in mods:
            if m.total_value >= 0 and m.display_in_string:
                if ret.strip():
                    ret += ", "
                ret += m.column2_output
        negatives = 0
        for m in mods:
            if m.total_value < 0 and m.display_in_string:
                negatives += 1
                ret += "; " if negatives == 1 else ", "
                ret += m.column2_output
        return ret

    @property
    def modifier_string(self) -> str:
        """Only the PRIVATE modifiers, plus the framework's shared ones.

        Ported from ``NakedModifier.getModifierString``. The inverse of
        `_naked_modifier_string`: what a Naked Advantage sells is its subject,
        so the trailing modifier list holds only what is private to it.
        """
        mods = [m for m in self._assigned_modifiers if m.private]
        parent = self.parent
        if parent is not None and _show_common_limitations():
            from kirby_cost.objects.frameworks import is_multipower
            for mod in parent.assigned_modifiers:
                if "VPP" in (mod.types or []):
                    continue
                if mod.xmlid == "CHARGES" and is_multipower(parent):
                    continue
                shared = (mod.total_value < 0
                          or type(parent).__name__ == "VariablePowerPool")
                already = GenericObject.find_object_by_id(
                    self._assigned_modifiers, mod.xmlid)
                generic = mod.xmlid in ("GENERIC_OBJECT", "CUSTOM_MODIFIER",
                                        "MODIFIER")
                if shared and (already is None or generic):
                    mods.append(mod)
        mods.sort(key=lambda m: m.total_value)

        ret = ""
        for m in mods:
            if m.total_value >= 0 and m.display_in_string:
                ret += ", " + m.column2_output
        if self.display_active_cost and (
                self.active_cost != self.total_cost
                or self.real_cost != self.total_cost):
            ret += f" ({round_up(self.active_cost)} Active Points)"
        negatives = 0
        for m in mods:
            if m.total_value < 0 and m.display_in_string:
                negatives += 1
                ret += "; " if negatives == 1 else ", "
                ret += m.column2_output
        return ret

    @property
    def column2_output(self) -> str:
        """``Reduced Endurance (0 END; +1/2) for up to 30 Active Points``.

        Ported from ``NakedModifier.getColumn2Output``. This inherited Power's
        line, which leads with the alias and the damage display, so it printed
        "Naked Advantage:  STR, Reduced Endurance (0 END; +1/2)" — the
        advantage demoted to a trailing modifier on a power that does not
        exist. HD leads with the advantage itself and says what it is bought
        FOR: the alias only appears when there is no input to name.
        """
        ret = self._naked_modifier_string()
        if self.input and self.input.strip():
            ret += (f" for up to {self._levels} Active Points of {self.input}")
        else:
            ret = (f"{self.alias or ''}: {ret} for up to {self._levels} "
                   f"Active Points")
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        ret = ret.strip()
        adders = self.adder_string
        if adders.strip():
            ret += f" ({adders})"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
