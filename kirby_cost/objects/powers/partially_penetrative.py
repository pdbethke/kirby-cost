"""
Partially Penetrative power class for kirby-cost.

Converted from com.hero.objects.powers.PartiallyPenetrative.java

Partially Penetrative sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class PartiallyPenetrative(SenseAdder, xmlid="PARTIALLYPENETRATIVE"):
    """
    Partially Penetrative power.
    
    Sense adder for partially penetrative sense.
    """
    
    def __init__(self):
        """Initialize a Partially Penetrative power."""
        super().__init__(PartiallyPenetrative.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Partially Penetrative)."""
        return ""

