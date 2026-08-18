"""
Compound Power class for kirby-cost.

Converted from com.hero.objects.powers.CompoundPower.java

Power that combines multiple powers together.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.char_affecting import CharAffectingObject
from typing import List


class CompoundPower(Power, xmlid="COMPOUNDPOWER"):
    """
    Compound Power.
    
    Combines multiple powers into a single power.
    """
    
    def __init__(self):
        """Initialize a Compound Power."""
        super().__init__()
        self.xmlid = CompoundPower.XMLID
        self.list_separator: str = " <b>plus</b> "
        self.powers: List[GenericObject] = []
    
    # ═══════════════════════════════════════════════════════════
    #  Cost calculations — delegates to sub-powers
    #  Ported from CompoundPower.java
    # ═══════════════════════════════════════════════════════════

    @property
    def total_cost(self) -> float:
        """Sum of sub-power total costs."""
        d = 0.0
        for obj in self.powers:
            obj.parent = self._parent
            d += obj.total_cost
            obj.parent = None
        return d

    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""


        return self._compute_active_cost()



    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """Sum of sub-power active costs."""
        d = 0.0
        for obj in self.powers:
            obj.parent = self._parent
            d += obj.active_cost
            obj.parent = None
        return d

    @property
    def real_cost_pre_list(self) -> float:
        """Sum of sub-power real costs, plus quantity cost."""
        d = 0.0
        if self._quantity > 1:
            qty_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                qty_cost += 5
                qty /= 2.0
            d += float(qty_cost)
        for obj in self.powers:
            obj.parent = self._parent
            d += obj.real_cost_pre_list
            obj.parent = None
        return d

    def get_save_xml(self):
        """Serialize compound power including sub-powers."""
        element = self.get_general_save_xml()
        for sub in self.powers:
            sub_elem = sub.save_xml()
            if sub_elem is not None:
                element.append(sub_elem)
        return element

    def affects_characteristics(self) -> bool:
        """Check if any combined power affects characteristics."""
        for power in self.powers:
            if isinstance(power, CharAffectingObject):
                cao = power
                if (cao.str_increase != 0.0 or
                    cao.get_dex_increase() != 0.0 or
                    cao.get_con_increase() != 0.0 or
                    cao.get_body_increase() != 0.0 or
                    cao.get_int_increase() != 0.0 or
                    cao.get_ego_increase() != 0.0 or
                    cao.get_pre_increase() != 0.0 or
                    cao.get_com_increase() != 0.0 or
                    cao.pd_increase != 0.0 or
                    cao.ed_increase != 0.0 or
                    cao.get_spd_increase() != 0.0 or
                    cao.get_rec_increase() != 0.0 or
                    cao.get_end_increase() != 0.0 or
                    cao.get_stun_increase() != 0.0 or
                    cao.get_def_increase() != 0.0 or
                    cao.get_size_increase() != 0.0 or
                    cao.get_running_increase() != 0.0 or
                    cao.get_swimming_increase() != 0.0 or
                    cao.get_leaping_increase() != 0.0):
                    return True
        return False

