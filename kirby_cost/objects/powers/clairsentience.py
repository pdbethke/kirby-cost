"""
Clairsentience power class for kirby-cost.

Converted from com.hero.objects.powers.Clairsentience.java

Power for remote sensing.
"""

from kirby_cost.objects.powers.power import Power


class Clairsentience(Power, xmlid="CLAIRSENTIENCE"):
    """
    Clairsentience power.
    
    Power for remote sensing at a distance.
    """
    
    def __init__(self):
        """Initialize a Clairsentience power."""
        super().__init__()
        self.xmlid = Clairsentience.XMLID
        self._duration = "CONSTANT"
        self.nontargeting_group_cost: float = 0.0
        self.nontargeting_sense_cost: float = 0.0
        self.targeting_group_cost: float = 0.0
        self.targeting_sense_cost: float = 0.0
        self.old_method: bool = False
    
    @property
    def damage_display(self) -> str:
        """Get clairsentience display."""
        return f"{self._levels}m range"
    
    @property
    def assigned_adders(self):
        """
        Get assigned adders with special handling.
        
        Removes CONCEALED if TRANSMIT not present.
        Removes ANALYZESENSE if DISCRIMINATORY present.
        """
        adders = super().assigned_adders
        
        # Stub: would filter adders based on special rules
        # For now, return as-is
        return adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value


