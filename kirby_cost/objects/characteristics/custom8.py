"""
Custom8 characteristic class.

Converted from com.hero.objects.characteristics.Custom8.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom8(Characteristic, xmlid="CUSTOM8"):
    """Custom8 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom8."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM8)

