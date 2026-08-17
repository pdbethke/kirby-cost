"""
Analyze Sense power class for kirby-cost.

Converted from com.hero.objects.powers.AnalyzeSense.java

Analyze sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class AnalyzeSense(SenseAdder, xmlid="ANALYZESENSE"):
    """
    Analyze Sense power.
    
    Sense adder that provides analysis ability.
    """
    
    def __init__(self):
        """Initialize an Analyze Sense power."""
        super().__init__(AnalyzeSense.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Analyze Sense)."""
        return ""
    
    @property
    def assigned_adders(self):
        """
        Get assigned adders with special handling.
        
        Removes GROUP adders that conflict with selected option.
        """
        # Stub: would filter adders based on special rules
        return super().assigned_adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value


