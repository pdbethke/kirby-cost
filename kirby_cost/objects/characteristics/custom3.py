"""
Custom3 characteristic class.

Converted from com.hero.objects.characteristics.Custom3.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom3(Characteristic, xmlid="CUSTOM3"):
    """Custom3 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom3."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM3)

