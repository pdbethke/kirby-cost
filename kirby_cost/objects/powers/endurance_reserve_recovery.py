"""
Endurance Reserve Recovery power class for kirby-cost.

Converted from com.hero.objects.powers.EnduranceReserveRecovery.java

Recovery rate for Endurance Reserve.
"""

from kirby_cost.objects.powers.power import Power


class EnduranceReserveRecovery(Power, xmlid="ENDURANCERESERVEREC"):
    """
    Endurance Reserve Recovery power.
    
    Defines recovery rate for Endurance Reserve.
    """
    
    def __init__(self):
        """Initialize an Endurance Reserve Recovery power."""
        super().__init__()
        self.xmlid = EnduranceReserveRecovery.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for END Reserve Recovery)."""
        return ""

