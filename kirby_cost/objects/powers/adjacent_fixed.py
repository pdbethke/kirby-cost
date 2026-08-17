"""
Adjacent Fixed power class for kirby-cost.

Converted from com.hero.objects.powers.AdjacentFixed.java

Adjacent Fixed sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class AdjacentFixed(SenseAdder, xmlid="ADJACENTFIXED"):
    """
    Adjacent Fixed power.
    
    Sense adder for adjacent fixed range.
    """
    
    def __init__(self):
        """Initialize an Adjacent Fixed power."""
        super().__init__(AdjacentFixed.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Adjacent Fixed)."""
        return ""

