"""
Missile Deflection power class for kirby-cost.

Converted from com.hero.objects.powers.MissileDeflection.java

Ability to deflect missiles.
"""

from kirby_cost.objects.powers.power import Power


class MissileDeflection(Power, xmlid="MISSILEDEFLECTION"):
    """
    Missile Deflection power.
    
    Ability to deflect missiles.
    """
    
    def __init__(self):
        """Initialize a Missile Deflection power."""
        super().__init__()
        self.xmlid = MissileDeflection.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get deflection display."""
        return f"{self._levels} Active Points' worth"

    def effective_target(self) -> str:
        """Java MissileDeflection.getTarget (MissileDeflection.java:146):
        with the REFLECTION adder the power targets DCV."""
        from kirby_cost.objects.base import GenericObject
        if GenericObject.find_object_by_id(self.assigned_adders, "REFLECTION") is not None:
            return "DCV"
        return super().effective_target()
    
    @property
    def active_cost(self) -> float:
        """
        Calculate active cost for Missile Deflection.
        
        Special handling for Reflection adder with RANGED modifier.
        """
        # Stub: would check for REFLECTION adder and RANGED modifier
        # For now, return standard active cost
        return super().active_cost

