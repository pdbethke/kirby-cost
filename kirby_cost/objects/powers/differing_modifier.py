"""
Differing Modifier power class for kirby-cost.

Converted from com.hero.objects.powers.DifferingModifier.java

Differing modifier power.
"""

from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_down


class DifferingModifier(Power, xmlid="DIFFERINGMODIFIER"):
    """
    Differing Modifier power.
    
    Applies different modifiers to different parts of a power.
    """
    
    def __init__(self):
        """Initialize a Differing Modifier power."""
        super().__init__()
        self.xmlid = DifferingModifier.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Differing Modifier)."""
        return ""
    
    @property
    def active_cost(self) -> float:
        """
        Calculate active cost for Differing Modifier.
        
        Uses levels with advantages applied.
        """
        active_cost = float(self._levels)
        
        # Apply advantages
        modifier_sum = 0.0
        for mod in self.assigned_modifiers:
            if mod.total_value >= 0.0:
                modifier_sum += mod.total_value
        
        # Stub: would check parent list modifiers
        
        if modifier_sum > 0.0:
            active_cost = round_half_down(active_cost * (1.0 + modifier_sum))
        
        return active_cost

    @property
    def real_cost_pre_list(self) -> float:
        """Ported from DifferingModifier.getRealCostPreList.

        The shape is the ordinary one -- limitations divide the active
        cost, then the multiplier, then the quantity doublings -- with one
        line at the end that makes this power what it is: ``ret -=
        getLevels()``. A Differing Modifier's levels are the points of the
        underlying power it re-modifies, and the character has already
        paid for those; what he pays here is only the INCREMENT the new
        modifiers add. Five levels with no modifiers therefore cost 5
        active and 0 real.

        The base Power's real cost had no such subtraction, so this read 5
        where HD reads 0. Found by the kitchen-sink fixture, 2026-08-29: no
        corpus character had ever bought one.
        """
        ret = self.active_cost
        limitation_total = 0.0
        for mod in self.assigned_modifiers:
            if mod.total_value <= 0.0:
                limitation_total += mod.total_value

        parent = self._parent
        if parent is not None and hasattr(parent, "assigned_modifiers"):
            from kirby_cost.objects.frameworks.multipower import Multipower
            for mod in parent.assigned_modifiers:
                if mod.types and "VPP" in mod.types:
                    continue
                if mod.xmlid == "CHARGES" and isinstance(parent, Multipower):
                    continue
                if (GenericObject.find_object_by_id(self.assigned_modifiers, mod.xmlid) is None
                        or mod.xmlid in ("GENERIC_OBJECT", "CUSTOM_MODIFIER")):
                    if mod.total_value < 0.0:
                        limitation_total += mod.total_value

        if limitation_total != 0.0:
            ret = round_half_down(ret / (1.0 + abs(limitation_total)))

        if self.multiplier != 1.0:
            ret = round_half_down(ret * self.multiplier)
        elif parent is not None and getattr(parent, "multiplier", 1.0) != 1.0:
            ret = round_half_down(ret * parent.multiplier)

        if self._quantity > 1:
            q = float(self._quantity)
            doublings = 0
            while q > 1.0:
                doublings += 1
                q /= 2.0
            ret += doublings * 5

        ret -= self._levels
        return ret

    @property
    def column2_output(self) -> str:
        """``(5 Active Points) for up to 5 Points of Blast`` --
        DifferingModifier.getColumn2Output. The line leads with the modifier
        string rather than the alias, names the levels as points of the
        power given in INPUT, and falls back to the alias plus
        ``[unknown]`` when no input was recorded.
        """
        ret = self.modifier_string or ""
        if self.input and self.input.strip():
            ret += f" for up to {self._levels} Points of {self.input}"
        else:
            ret = f"{self.alias}: {ret} for up to {self._levels} Points of [unknown]"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        ret = ret.strip()
        adders = self.adder_string or ""
        if adders.strip():
            ret += f" ({adders})"
        return ret + self._end_reserve_note()
