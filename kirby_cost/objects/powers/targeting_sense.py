"""
Targeting Sense power class for kirby-cost.

Converted from com.hero.objects.powers.TargetingSense.java

Targeting sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class TargetingSense(SenseAdder, xmlid="TARGETINGSENSE"):
    """
    Targeting Sense power.
    
    Sense adder that allows targeting.
    """
    
    def __init__(self):
        """Initialize a Targeting Sense power."""
        super().__init__(TargetingSense.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Targeting Sense)."""
        return ""

