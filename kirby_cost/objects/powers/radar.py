"""
Radar power class for kirby-cost.

Converted from com.hero.objects.powers.Radar.java

Radar sense.
"""

from kirby_cost.objects.powers.sense import Sense


class Radar(Sense, xmlid="RADAR"):
    """
    Radar power.
    
    Sense for radar detection.
    """
    
    def __init__(self):
        """Initialize a Radar power."""
        super().__init__(Radar.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Radar)."""
        return ""

