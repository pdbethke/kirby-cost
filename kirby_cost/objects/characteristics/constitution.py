"""
Constitution characteristic class.

Converted from com.hero.objects.characteristics.Constitution.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Constitution(Characteristic, xmlid="CON"):
    """Constitution (CON) characteristic."""
    
    def __init__(self):
        """Initialize Constitution."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.CON)

