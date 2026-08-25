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
        """Get roll. Body.java:43-49 -- EMPTY in 6E.

        The edition check was left unfinished ("this would need to check the
        template version"), so this returned the base roll unconditionally and
        BODY printed "12-" where HD prints nothing. `is_6e()` is the check the
        rest of the engine uses.
        """
        from kirby_cost.objects.base import is_6e
        if is_6e():
            return ""
        return super().roll(active_hero)

