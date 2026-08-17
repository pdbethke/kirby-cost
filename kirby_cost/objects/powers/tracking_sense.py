"""
Tracking Sense power class for kirby-cost.

Converted from com.hero.objects.powers.TrackingSense.java

Tracking sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class TrackingSense(SenseAdder, xmlid="TRACKINGSENSE"):
    """
    Tracking Sense power.
    
    Sense adder that allows tracking.
    """
    
    def __init__(self):
        """Initialize a Tracking Sense power."""
        super().__init__(TrackingSense.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Tracking Sense)."""
        return ""

