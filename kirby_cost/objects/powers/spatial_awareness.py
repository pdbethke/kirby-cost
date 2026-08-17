"""
Spatial Awareness power class for kirby-cost.

Converted from com.hero.objects.powers.SpatialAwareness.java

Spatial awareness sense.
"""

from kirby_cost.objects.powers.sense import Sense


class SpatialAwareness(Sense, xmlid="SPATIALAWARENESS"):
    """
    Spatial Awareness power.
    
    Sense for spatial awareness.
    """
    
    def __init__(self):
        """Initialize a Spatial Awareness power."""
        super().__init__(SpatialAwareness.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Spatial Awareness)."""
        return ""

