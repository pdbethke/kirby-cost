"""
OMCV (Offensive Mental Combat Value) characteristic class.

Converted from com.hero.objects.characteristics.OMCV.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class OMCV(Characteristic, xmlid="OMCV"):
    """OMCV (Offensive Mental Combat Value) characteristic."""
    
    def __init__(self):
        """Initialize OMCV."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.OMCV)
    
    def roll(self, active_hero=None):
        """OMCV doesn't have a roll."""
        return ""

