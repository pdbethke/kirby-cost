"""
Teleportation power class for kirby-cost.

Converted from com.hero.objects.powers.Teleportation.java

Teleportation is a movement power that allows instant travel.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class Teleportation(Power, xmlid="TELEPORTATION"):
    """
    Teleportation power.
    
    Movement power that allows instant travel through space.
    """
    
    def __init__(self):
        """Initialize a Teleportation power."""
        super().__init__()
        self.xmlid = Teleportation.XMLID
        self.affects_primary = True
        self._duration = "INSTANT"
    
    @property
    def damage_display(self) -> str:
        """
        Get movement display string.
        
        Format: "Xm" (6E) or "X\"" (5E)
        """
        movement = int(round_down(float(self._levels)))
        
        # Stub: would check if 6E
        is_6e = True  # Default to 6E
        
        if is_6e:
            return f"{movement}m"
        else:
            return f'{movement}"'
    
    @property
    def summable(self) -> bool:
        """Check if Teleportation can be summed with other movement powers."""
        return True

