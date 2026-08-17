"""
Transmit power class for kirby-cost.

Converted from com.hero.objects.powers.Transmit.java

Transmit sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class Transmit(SenseAdder, xmlid="TRANSMIT"):
    """
    Transmit power.
    
    Sense adder that allows transmission.
    """
    
    def __init__(self):
        """Initialize a Transmit power."""
        super().__init__(Transmit.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Transmit)."""
        return ""

