"""
Infrared Perception power class for kirby-cost.

Converted from com.hero.objects.powers.InfraredPerception.java

Infrared perception sense.
"""

from kirby_cost.objects.powers.sense import Sense


class InfraredPerception(Sense, xmlid="INFRAREDPERCEPTION"):
    """
    Infrared Perception power.
    
    Sense for infrared light perception.
    """
    
    def __init__(self):
        """Initialize an Infrared Perception power."""
        super().__init__(InfraredPerception.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Infrared Perception)."""
        return ""

