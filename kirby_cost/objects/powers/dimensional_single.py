"""
Dimensional Single power class for kirby-cost.

Converted from com.hero.objects.powers.DimensionalSingle.java

Dimensional Single sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class DimensionalSingle(SenseAdder, xmlid="DIMENSIONALSINGLE"):
    """
    Dimensional Single power.
    
    Sense adder for single dimension.
    """
    
    def __init__(self):
        """Initialize a Dimensional Single power."""
        super().__init__(DimensionalSingle.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Dimensional Single)."""
        return ""

