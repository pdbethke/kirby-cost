"""
Nightvision power class for kirby-cost.

Converted from com.hero.objects.powers.Nightvision.java

Nightvision sense.
"""

from kirby_cost.objects.powers.sense import Sense


class Nightvision(Sense, xmlid="NIGHTVISION"):
    """
    Nightvision power.
    
    Sense for seeing in darkness.
    """
    
    def __init__(self):
        """Initialize a Nightvision power."""
        super().__init__(Nightvision.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Nightvision)."""
        return ""

