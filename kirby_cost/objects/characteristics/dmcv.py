"""
DMCV (Defensive Mental Combat Value) characteristic class.

Converted from com.hero.objects.characteristics.DMCV.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class DMCV(Characteristic, xmlid="DMCV"):
    """DMCV (Defensive Mental Combat Value) characteristic."""
    
    def __init__(self):
        """Initialize DMCV."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.DMCV)
    
    def roll(self, active_hero=None):
        """DMCV doesn't have a roll."""
        return ""

