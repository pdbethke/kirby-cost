"""
Shapeshift power class for kirby-cost.

Converted from com.hero.objects.powers.Shapeshift.java

Power to change shape.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class Shapeshift(SenseAffectingPower, xmlid="SHAPESHIFT"):
    """
    Shapeshift power.
    
    Power to change physical form.
    """
    
    def __init__(self):
        """Initialize a Shapeshift power."""
        super().__init__()
        self.xmlid = Shapeshift.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get shapeshift display."""
        return f"{self._levels} points"
    
    @property
    def assigned_adders(self):
        """
        Get assigned adders with cost adjustments for 6E.
        
        In 6E, different sense groups have different costs.
        """
        adders = super().assigned_adders
        
        # Stub: would check if 6E and adjust costs based on sense type
        # For now, return as-is
        return adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value


