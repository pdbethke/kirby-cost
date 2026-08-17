"""
Invisibility power class for kirby-cost.

Converted from com.hero.objects.powers.Invisibility.java

Invisibility makes the character invisible to certain sense groups.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class Invisibility(SenseAffectingPower, xmlid="INVISIBILITY"):
    """
    Invisibility power.
    
    Makes the character invisible to specified sense groups.
    """
    
    def __init__(self):
        """Initialize an Invisibility power."""
        super().__init__()
        self.xmlid = Invisibility.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Invisibility)."""
        return ""

