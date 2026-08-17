"""
Radio Perception power class for kirby-cost.

Converted from com.hero.objects.powers.RadioPerception.java

Radio perception sense.
"""

from kirby_cost.objects.powers.sense import Sense


class RadioPerception(Sense, xmlid="RADIOPERCEPTION"):
    """
    Radio Perception power.
    
    Sense for radio wave perception.
    """
    
    def __init__(self):
        """Initialize a Radio Perception power."""
        super().__init__(RadioPerception.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Radio Perception)."""
        return ""

