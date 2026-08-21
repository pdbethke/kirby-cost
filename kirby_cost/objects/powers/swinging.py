"""
Swinging power class for kirby-cost.

Converted from com.hero.objects.powers.Swinging.java

Movement power for swinging on lines.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import is_6e
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
        # Java is roundDown(getLevels()) -- the levels ARE the metres, and
        # nothing divides by levelValue (Swinging.java:39). Swinging costs 1
        # per 2m, so dividing halved every distance: 20m of Swinging bought
        # for 10 points printed as "10m".
        movement = int(round_down(float(self.levels)))
        return f"{movement}m" if is_6e() else f'{movement}"'
    
    @property
    def summable(self) -> bool:
        """Check if can be summed with other movement powers."""
        return True

