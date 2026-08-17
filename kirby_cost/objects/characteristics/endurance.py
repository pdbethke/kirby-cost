"""
Endurance characteristic class.

Converted from com.hero.objects.characteristics.Endurance.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Endurance(Characteristic, xmlid="END"):
    """Endurance (END) characteristic."""
    
    def __init__(self):
        """Initialize Endurance."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.END)
    
    def roll(self, active_hero=None):
        """Endurance doesn't have a roll."""
        return ""

