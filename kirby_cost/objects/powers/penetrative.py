"""
Penetrative power class for kirby-cost.

Converted from com.hero.objects.powers.Penetrative.java

Penetrative sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class Penetrative(SenseAdder, xmlid="PENETRATIVE"):
    """
    Penetrative power.
    
    Sense adder for penetrative sense.
    """
    
    def __init__(self):
        """Initialize a Penetrative power."""
        super().__init__(Penetrative.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Penetrative)."""
        return ""

