"""
Increased Arc 240 power class for kirby-cost.

Converted from com.hero.objects.powers.IncreasedArc240.java

Increased Arc 240 sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class IncreasedArc240(SenseAdder, xmlid="INCREASEDARC240"):
    """
    Increased Arc 240 power.
    
    Sense adder for 240-degree arc.
    """
    
    def __init__(self):
        """Initialize an Increased Arc 240 power."""
        super().__init__(IncreasedArc240.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Increased Arc 240)."""
        return ""

