"""
Make A Sense power class for kirby-cost.

Converted from com.hero.objects.powers.MakeASense.java

Make A Sense sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class MakeASense(SenseAdder, xmlid="MAKEASENSE"):
    """
    Make A Sense power.
    
    Sense adder that creates a new sense.
    """
    
    def __init__(self):
        """Initialize a Make A Sense power."""
        super().__init__(MakeASense.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Make A Sense)."""
        return ""

