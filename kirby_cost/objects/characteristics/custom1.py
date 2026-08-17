"""
Custom1 characteristic class.

Converted from com.hero.objects.characteristics.Custom1.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom1(Characteristic, xmlid="CUSTOM1"):
    """Custom1 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom1."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM1)

