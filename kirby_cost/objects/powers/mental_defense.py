"""
Mental Defense power class for kirby-cost.

Converted from com.hero.objects.powers.MentalDefense.java

Defense against mental attacks.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_down, round_half_up


class MentalDefense(Power, xmlid="MENTALDEFENSE"):
    """
    Mental Defense power.
    
    Defense against mental attacks.
    """
    
    def __init__(self):
        """Initialize a Mental Defense power."""
        super().__init__()
        self.xmlid = MentalDefense.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get mental defense display."""
        return f"{self._levels} points"
    
    @property
    def active_cost(self) -> float:
        """
        Calculate active cost for Mental Defense.
        
        In 5E, includes EGO/5 bonus. In 6E, just base cost.
        """
        total_cost = self.total_cost
        
        # Stub: would check if 6E and get EGO characteristic
        # For now, return standard active cost
        return super().active_cost

