"""
Custom9 characteristic class.

Converted from com.hero.objects.characteristics.Custom9.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom9(Characteristic, xmlid="CUSTOM9"):
    """Custom9 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom9."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM9)

