"""
Custom2 characteristic class.

Converted from com.hero.objects.characteristics.Custom2.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom2(Characteristic, xmlid="CUSTOM2"):
    """Custom2 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom2."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM2)

