"""
Body characteristic class.

Converted from com.hero.objects.characteristics.Body.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Body(Characteristic, xmlid="BODY"):
    """Body (BODY) characteristic."""
    
    def __init__(self):
        """Initialize Body."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.BODY)
    
    def roll(self, active_hero=None):
        """Get roll (empty for 6E)."""
        # In 6E, BODY doesn't have a roll
        # This would need to check the template version
        return super().roll(active_hero)

