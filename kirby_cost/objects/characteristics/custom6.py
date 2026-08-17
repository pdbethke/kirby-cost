"""
Custom6 characteristic class.

Converted from com.hero.objects.characteristics.Custom6.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom6(Characteristic, xmlid="CUSTOM6"):
    """Custom6 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom6."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM6)

