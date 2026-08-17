"""
Change Environment power class for kirby-cost.

Converted from com.hero.objects.powers.ChangeEnvironment.java

Power to change the environment.
"""

from kirby_cost.objects.powers.power import Power


class ChangeEnvironment(Power, xmlid="CHANGEENVIRONMENT"):
    """
    Change Environment power.
    
    Alters the environment in various ways.
    """
    
    def __init__(self):
        """Initialize a Change Environment power."""
        super().__init__()
        self.xmlid = ChangeEnvironment.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get change environment display."""
        return f"{self._levels}d6"
    
    def can_add(self, adder) -> bool:
        """
        Check if adder can be added.
        
        Special logic for MULTIPLECOMBATEFFECTS, VARYINGCOMBATEFFECTS, LONG.
        """
        can_add = super().can_add(adder)
        if not can_add:
            return False
        
        # Stub: would check for MULTIPLECOMBATEFFECTS logic
        return True

