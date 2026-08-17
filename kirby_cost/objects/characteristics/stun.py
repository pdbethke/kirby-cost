"""
Stun characteristic class.

Converted from com.hero.objects.characteristics.Stun.java
"""

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType


class Stun(Characteristic, xmlid="STUN"):
    """Stun (STUN) characteristic."""
    
    def __init__(self):
        """Initialize Stun."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.STUN)
    
    def roll(self, active_hero=None):
        """Stun doesn't have a roll."""
        return ""
    
    @property
    def display_notes(self) -> str:
        """Stun doesn't have display notes."""
        return ""

