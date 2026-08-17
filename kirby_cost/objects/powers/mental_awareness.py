"""
Mental Awareness power class for kirby-cost.

Converted from com.hero.objects.powers.MentalAwareness.java

Mental awareness sense.
"""

from kirby_cost.objects.powers.sense import Sense


class MentalAwareness(Sense, xmlid="MENTALAWARENESS"):
    """
    Mental Awareness power.
    
    Sense for detecting mental powers.
    """
    
    def __init__(self):
        """Initialize a Mental Awareness power."""
        super().__init__(MentalAwareness.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Mental Awareness)."""
        return ""
    
    @property
    def base_cost(self) -> float:
        """
        Get base cost for Mental Awareness.

    @base_cost.setter
    def base_cost(self, value) -> None:
        self._base_cost = value
        
        In 5E, returns 0 if character has mental powers that provide awareness.
        """
        # Stub: would check for mental powers in 5E
        # For now, return standard base cost
        return super().base_cost

