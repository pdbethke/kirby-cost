"""
Concealed power class for kirby-cost.

Converted from com.hero.objects.powers.Concealed.java

Concealed sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class Concealed(SenseAdder, xmlid="CONCEALED"):
    """
    Concealed power.
    
    Sense adder that makes sense concealed.
    """
    
    def __init__(self):
        """Initialize a Concealed power."""
        super().__init__(Concealed.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Concealed)."""
        return ""
    
    @property
    def assigned_adders(self):
        """
        Get assigned adders with special handling.
        
        Removes GROUP adders that conflict with selected option or TRANSMIT.
        """
        # Stub: would filter adders based on special rules
        return super().assigned_adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value


