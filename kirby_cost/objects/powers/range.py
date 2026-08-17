"""
Range power class for kirby-cost.

Converted from com.hero.objects.powers.Range.java

Range sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class Range(SenseAdder, xmlid="RANGE"):
    """
    Range power.
    
    Sense adder that provides range.
    """
    
    def __init__(self):
        """Initialize a Range power."""
        super().__init__(Range.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Range)."""
        return ""

