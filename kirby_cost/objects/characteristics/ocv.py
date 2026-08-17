"""
OCV (Offensive Combat Value) characteristic class.

Converted from com.hero.objects.characteristics.OCV.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class OCV(Characteristic, xmlid="OCV"):
    """OCV (Offensive Combat Value) characteristic."""
    
    def __init__(self):
        """Initialize OCV."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.OCV)
    
    def roll(self, active_hero=None):
        """OCV doesn't have a roll."""
        return ""

