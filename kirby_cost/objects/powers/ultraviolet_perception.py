"""
Ultraviolet Perception power class for kirby-cost.

Converted from com.hero.objects.powers.UltravioletPerception.java

Ultraviolet perception sense.
"""

from kirby_cost.objects.powers.sense import Sense


class UltravioletPerception(Sense, xmlid="ULTRAVIOLETPERCEPTION"):
    """
    Ultraviolet Perception power.
    
    Sense for ultraviolet light perception.
    """
    
    def __init__(self):
        """Initialize an Ultraviolet Perception power."""
        super().__init__(UltravioletPerception.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Ultraviolet Perception)."""
        return ""

