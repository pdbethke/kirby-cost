"""
Custom4 characteristic class.

Converted from com.hero.objects.characteristics.Custom4.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom4(Characteristic, xmlid="CUSTOM4"):
    """Custom4 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom4."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM4)

