"""
N-Ray Perception power class for kirby-cost.

Converted from com.hero.objects.powers.NRayPerception.java

N-Ray perception sense.
"""

from kirby_cost.objects.powers.sense import Sense


class NRayPerception(Sense, xmlid="NRAYPERCEPTION"):
    """
    N-Ray Perception power.
    
    Sense for N-Ray perception.
    """
    
    def __init__(self):
        """Initialize an N-Ray Perception power."""
        super().__init__(NRayPerception.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for N-Ray Perception)."""
        return ""

