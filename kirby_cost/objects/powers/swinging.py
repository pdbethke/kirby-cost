"""
Swinging power class for kirby-cost.

Converted from com.hero.objects.powers.Swinging.java

Movement power for swinging on lines.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class Swinging(Power, xmlid="SWINGING"):
    """
    Swinging power.
    
    Movement power for swinging on lines.
    """
    
    def __init__(self):
        """Initialize a Swinging power."""
        super().__init__()
        self.xmlid = Swinging.XMLID
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

