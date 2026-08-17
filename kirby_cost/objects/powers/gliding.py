"""
Gliding power class for kirby-cost.

Converted from com.hero.objects.powers.Gliding.java

Movement power for gliding.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class Gliding(Power, xmlid="GLIDING"):
    """
    Gliding power.
    
    Movement power for gliding through the air.
    """
    
    def __init__(self):
        """Initialize a Gliding power."""
        super().__init__()
        self.xmlid = Gliding.XMLID
        self.affects_primary = True
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get movement display string."""
        movement = int(round_down(float(self._levels) / self._level_value)) if self._level_value != 0.0 else self._levels
        is_6e = True  # Stub: would check if 6E
        return f"{movement}m" if is_6e else f'{movement}"'
    
    @property
    def summable(self) -> bool:
        """Check if can be summed with other movement powers."""
        return True

