"""
DCV (Defensive Combat Value) characteristic class.

Converted from com.hero.objects.characteristics.DCV.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class DCV(Characteristic, xmlid="DCV"):
    """DCV (Defensive Combat Value) characteristic."""
    
    def __init__(self):
        """Initialize DCV."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.DCV)
    
    def roll(self, active_hero=None):
        """DCV doesn't have a roll."""
        return ""

