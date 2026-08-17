"""
Dimensional All power class for kirby-cost.

Converted from com.hero.objects.powers.DimensionalAll.java

Dimensional All sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class DimensionalAll(SenseAdder, xmlid="DIMENSIONALALL"):
    """
    Dimensional All power.
    
    Sense adder for all dimensions.
    """
    
    def __init__(self):
        """Initialize a Dimensional All power."""
        super().__init__(DimensionalAll.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Dimensional All)."""
        return ""

