"""
Differing Modifier power class for kirby-cost.

Converted from com.hero.objects.powers.DifferingModifier.java

Differing modifier power.
"""

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

