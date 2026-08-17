"""
Def characteristic class.

Converted from com.hero.objects.characteristics.Def.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class DefChar(Characteristic, xmlid="DEF"):
    """Def (DEF) characteristic."""
    
    def __init__(self):
        """Initialize Def."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.DEF)
    
    def roll(self, active_hero=None):
        """Def doesn't have a roll."""
        return ""

