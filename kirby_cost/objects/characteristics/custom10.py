"""
Custom10 characteristic class.

Converted from com.hero.objects.characteristics.Custom10.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom10(Characteristic, xmlid="CUSTOM10"):
    """Custom10 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom10."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM10)

