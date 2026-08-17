"""
Custom5 characteristic class.

Converted from com.hero.objects.characteristics.Custom5.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Custom5(Characteristic, xmlid="CUSTOM5"):
    """Custom5 custom characteristic."""
    
    def __init__(self):
        """Initialize Custom5."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CUSTOM5)

