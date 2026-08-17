"""
Recovery characteristic class.

Converted from com.hero.objects.characteristics.Recovery.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Recovery(Characteristic, xmlid="REC"):
    """Recovery (REC) characteristic."""
    
    def __init__(self):
        """Initialize Recovery."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.REC)
    
    def roll(self, active_hero=None):
        """Recovery doesn't have a roll."""
        return ""

