"""
Increased Arc 360 power class for kirby-cost.

Converted from com.hero.objects.powers.IncreasedArc360.java

Increased Arc 360 sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class IncreasedArc360(SenseAdder, xmlid="INCREASEDARC360"):
    """
    Increased Arc 360 power.
    
    Sense adder for 360-degree arc.
    """
    
    def __init__(self):
        """Initialize an Increased Arc 360 power."""
        super().__init__(IncreasedArc360.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Increased Arc 360)."""
        return ""

