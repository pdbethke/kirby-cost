"""
Fixed Location power class for kirby-cost.

Converted from com.hero.objects.powers.FixedLocation.java

Fixed hit locations power.
"""

from kirby_cost.objects.powers.power import Power


class FixedLocation(Power, xmlid="FIXEDLOCATION"):
    """
    Fixed Location power.
    
    Provides fixed hit locations.
    """
    
    def __init__(self):
        """Initialize a Fixed Location power."""
        super().__init__()
        self.xmlid = FixedLocation.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get location display."""
        return f"({self._levels} Locations)"

