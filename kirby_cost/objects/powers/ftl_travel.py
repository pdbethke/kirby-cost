"""
FTL Travel power class for kirby-cost.

Converted from com.hero.objects.powers.FTLTravel.java

Faster-than-light travel power.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down, round_half_up
import math


class FTLTravel(Power, xmlid="FTL"):
    """
    FTL Travel power.
    
    Faster-than-light travel power.
    """
    
    def __init__(self):
        """Initialize an FTL Travel power."""
        super().__init__()
        self.xmlid = FTLTravel.XMLID
        self._duration = "INSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get FTL travel display string."""
        d = math.pow(self.level_power, round_down(float(self._levels) / self._level_value))
        
        # Determine time unit
        time_unit = "year"
        if d > 31536000.0:
            time_unit = "second"
            d /= 31536000.0
        elif d > 525600.0:
            time_unit = "minute"
            d /= 525600.0
        elif d > 8760.0:
            time_unit = "hour"
            d /= 8760.0
        elif d > 365.0:
            time_unit = "day"
            d /= 365.0
        elif d > 52.0:
            time_unit = "week"
            d /= 52.0
        elif d > 12.0:
            time_unit = "month"
            d /= 12.0
        
        d = round_half_up(d)
        
        if d > 1.0 or time_unit != "year":
            return f"({d:,.0f} Light Years/{time_unit})"
        return ""

