"""
Stretching power class for kirby-cost.

Converted from com.hero.objects.powers.Stretching.java

Power to extend limbs/body.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class Stretching(Power, xmlid="STRETCHING"):
    """
    Stretching power.
    
    Power to extend limbs/body.
    """
    
    def __init__(self):
        """Initialize a Stretching power."""
        super().__init__()
        self.xmlid = Stretching.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get reach display string."""
        movement = int(round_down(float(self._levels) / self._level_value)) if self._level_value != 0.0 else self._levels
        is_6e = True  # Stub: would check if 6E
        return f"{movement}m" if is_6e else f'{movement}"'

