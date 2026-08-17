"""
Endurance Reserve power class for kirby-cost.

Converted from com.hero.objects.powers.EnduranceReserve.java

Reserve of END points with a separate Recovery component.
The Reserve and Recovery can share modifiers (recIsSamePower) or be separate.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_down
from kirby_cost.objects.frameworks import is_multipower, is_elemental_control
from kirby_cost.objects.modifiers.linked import is_linked
from typing import Optional


class EnduranceReserve(Power, xmlid="ENDURANCERESERVE"):
    """
    Endurance Reserve power.

    Has two components: the reserve (END pool) and recovery (REC rate).
    If both have identical modifiers, they're treated as one power for cost purposes.
    """

    def __init__(self):
        super().__init__()
        self.xmlid = EnduranceReserve.XMLID
        self._duration = "CONSTANT"
        self.rec: Optional[GenericObject] = None  # EnduranceReserveRecovery

    def get_save_xml(self):
        """Serialize endurance reserve including recovery component."""
        element = self.get_general_save_xml()
        if self.rec is not None:
            rec_elem = self.rec.get_save_xml()
            if rec_elem is not None:
                element.append(rec_elem)
        return element

    @property
    def damage_display(self) -> str:
        return f"{self._levels} END"

    def rec_is_same_power(self) -> bool:
        """
        Check if recovery has the same modifiers as the reserve.

        If both components have identical modifier sets, they share cost calculations.
        Ported from EnduranceReserve.java recIsSamePower().
        """
        if self.rec is None:
            return False

        my_mods = self.assigned_modifiers
        rec_mods = self.rec.assigned_modifiers

        if len(my_mods) != len(rec_mods):
            return False

        # Compare each modifier's column2 output (Java uses this for equality)
        for i in range(len(my_mods)):
            my_col2 = ""
            rec_col2 = ""
            if hasattr(my_mods[i], 'column2_output'):
                my_col2 = my_mods[i].column2_output
            if hasattr(rec_mods[i], 'column2_output'):
                rec_col2 = rec_mods[i].column2_output
            if my_col2 != rec_col2:
                return False

        return True

    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""


        return self._compute_active_cost()



    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """
        Calculate active cost for END Reserve.

        If recovery is same power, add its total cost before applying advantages.
        Otherwise, add recovery's active cost separately after.

        Ported from EnduranceReserve.java getActiveCost().
        """
        same_power = self.rec_is_same_power()

        # Start with reserve's total cost (calls GenericObject.getTotalCost via super)
        d = super().total_cost

        if same_power and self.rec is not None:
            d += self.rec.total_cost

        # Sum positive advantages
        modifier_sum = 0.0
        has_advantages = False

        for mod in self.assigned_modifiers:
            if mod.total_value > 0.0:
                modifier_sum += mod.total_value
                has_advantages = True

        # Parent list advantages
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent
        if parent:
            for mod in parent.assigned_modifiers:
                if mod.types and "VPP" in mod.types:
                    continue
                if mod.xmlid == "CHARGES" and is_multipower(parent):
                    continue
                if is_linked(mod):
                    continue
                if mod.total_value <= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, mod.xmlid) and
                    mod.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                if is_multipower(parent) or is_elemental_control(parent):
                    continue
                modifier_sum += mod.total_value
                has_advantages = True

        result = d * (1.0 + modifier_sum)

        # Set recovery's parent list for its own calculations
        if self.rec is not None:
            self.rec.parent = self._parent

        if has_advantages:
            result = round_half_down(result)

        # If not same power, add recovery's active cost separately
        if not same_power and self.rec is not None:
            result += self.rec.active_cost

        return result

    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost for END Reserve.

        If same power, apply limitations to combined active cost.
        Otherwise, add recovery's real cost separately.

        Ported from EnduranceReserve.java getRealCostPreList().
        """
        same_power = self.rec_is_same_power()

        # Use combined active cost if same power, else just reserve's active
        if same_power:
            d = self.active_cost
        else:
            # Get just the reserve's active cost (without recovery)
            d = super()._compute_active_cost()

        # Sum negative limitations
        limitation_sum = 0.0
        has_limitations = False

        for mod in self.assigned_modifiers:
            if mod.total_value < 0.0:
                limitation_sum += mod.total_value
                has_limitations = True

        # Parent list limitations
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent
        if parent:
            for mod in parent.assigned_modifiers:
                if mod.types and "VPP" in mod.types:
                    continue
                if mod.xmlid == "CHARGES" and is_multipower(self._parent):
                    continue
                if mod.total_value >= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, mod.xmlid) and
                    mod.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                limitation_sum += mod.total_value
                has_limitations = True

        result = d / (1.0 + abs(limitation_sum))
        if has_limitations:
            result = round_half_down(result)

        # Set recovery's parent list
        if self.rec is not None:
            self.rec.parent = self._parent

        # If not same power, add recovery's real cost separately
        if not same_power and self.rec is not None:
            result += self.rec.real_cost_pre_list

        # Minimum 1 CP
        if result == 0.0 and d > 0.0:
            result = 1.0

        # Quantity cost
        if self._quantity > 1:
            qty_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                qty_cost += 5
                qty /= 2.0
            result += float(qty_cost)

        return result
