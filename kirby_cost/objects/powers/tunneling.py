"""
Tunneling power class for kirby-cost.

Converted from com.hero.objects.powers.Tunneling.java

Power to tunnel through materials.
"""

from kirby_cost.objects.powers.power import Power


class Tunneling(Power, xmlid="TUNNELING"):
    """
    Tunneling power.
    
    Power to tunnel through materials.
    """
    
    def __init__(self):
        """Initialize a Tunneling power."""
        super().__init__()
        self.xmlid = Tunneling.XMLID
        self.affects_primary = True
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get tunneling display string."""
        # Stub: would calculate movement and material
        return f"{self._levels}m through {self.input or 'material'}"

