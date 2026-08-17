"""
Speed Reading Talent for kirby-cost.

Converted from com.hero.objects.talents.SpeedReading.java

Speed Reading allows reading at increased speeds.
"""

from typing import Optional
from kirby_cost.objects.talents.talent import Talent


class SpeedReading(Talent, xmlid="SPEED_READING"):
    """
    Speed Reading Talent.
    
    Allows reading at increased speeds.
    """
    
    def __init__(self, element=None):
        """Initialize a Speed Reading talent."""
        super().__init__(element, self.XMLID)
        self._levels = self._levels
    
    @property
    def levels(self) -> int:
        """Get the number of levels."""
        return self._levels

    @levels.setter
    def levels(self, levels: int) -> None:
        """
        Set levels and update alias with multiplier.

        Args:
            levels: Number of levels
        """
        self._levels = levels
        
        # Calculate multiplier: level_power^levels
        multiplier = int(self.level_power ** self._levels)
        alias = f"{self._display} (x{multiplier:,})"
        self._alias = alias



