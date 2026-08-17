"""
Floating Location power class for kirby-cost.

Converted from com.hero.objects.powers.FloatingLocation.java

Floating hit locations power.
"""

from kirby_cost.objects.powers.power import Power


class FloatingLocation(Power, xmlid="FLOATINGLOCATION"):
    """
    Floating Location power.
    
    Provides floating hit locations.
    """
    
    def __init__(self):
        """Initialize a Floating Location power."""
        super().__init__()
        self.xmlid = FloatingLocation.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get location display."""
        return f"({self._levels} Locations)"

