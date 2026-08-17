"""
Ultrasonic Perception power class for kirby-cost.

Converted from com.hero.objects.powers.UltrasonicPerception.java

Ultrasonic perception sense.
"""

from kirby_cost.objects.powers.sense import Sense


class UltrasonicPerception(Sense, xmlid="ULTRASONICPERCEPTION"):
    """
    Ultrasonic Perception power.
    
    Sense for ultrasonic sound perception.
    """
    
    def __init__(self):
        """Initialize an Ultrasonic Perception power."""
        super().__init__(UltrasonicPerception.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Ultrasonic Perception)."""
        return ""

