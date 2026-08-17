"""
High Range Radio Perception power class for kirby-cost.

Converted from com.hero.objects.powers.HighRangeRadioPerception.java

High range radio perception sense.
"""

from kirby_cost.objects.powers.sense import Sense


class HighRangeRadioPerception(Sense, xmlid="HRRP"):
    """
    High Range Radio Perception power.
    
    Sense for high range radio wave perception.
    """
    
    def __init__(self):
        """Initialize a High Range Radio Perception power."""
        super().__init__(HighRangeRadioPerception.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for High Range Radio Perception)."""
        return ""

