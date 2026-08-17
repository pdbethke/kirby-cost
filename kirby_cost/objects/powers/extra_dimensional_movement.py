"""
Extra-Dimensional Movement power class for kirby-cost.

Converted from com.hero.objects.powers.ExtraDimensionalMovement.java

Power to travel to other dimensions.
"""

from kirby_cost.objects.powers.power import Power


class ExtraDimensionalMovement(Power, xmlid="EXTRADIMENSIONALMOVEMENT"):
    """
    Extra-Dimensional Movement power.
    
    Power to travel to other dimensions.
    """
    
    def __init__(self):
        """Initialize an Extra-Dimensional Movement power."""
        super().__init__()
        self.xmlid = ExtraDimensionalMovement.XMLID
        self._duration = "INSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for EDM)."""
        return ""

