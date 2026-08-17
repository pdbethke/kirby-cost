"""
Custom7 characteristic class.

Converted from com.hero.objects.characteristics.Custom7.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom7(Characteristic, xmlid="CUSTOM7"):
    """Custom7 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom7."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM7)

