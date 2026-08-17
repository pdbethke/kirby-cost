"""
Dimensional Group power class for kirby-cost.

Converted from com.hero.objects.powers.DimensionalGroup.java

Dimensional Group sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class DimensionalGroup(SenseAdder, xmlid="DIMENSIONALGROUP"):
    """
    Dimensional Group power.
    
    Sense adder for dimension group.
    """
    
    def __init__(self):
        """Initialize a Dimensional Group power."""
        super().__init__(DimensionalGroup.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Dimensional Group)."""
        return ""

