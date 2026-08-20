"""
Darkness power class for kirby-cost.

Converted from com.hero.objects.powers.Darkness.java

Power to create darkness.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class Darkness(SenseAffectingPower, xmlid="DARKNESS"):
    """
    Darkness power.
    
    Creates darkness affecting sense groups.
    """
    
    def __init__(self):
        """Initialize a Darkness power."""
        super().__init__()
        self.xmlid = Darkness.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get darkness display."""
        return f"{self._levels}m radius"
    
