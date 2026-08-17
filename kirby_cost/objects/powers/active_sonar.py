"""
Active Sonar power class for kirby-cost.

Converted from com.hero.objects.powers.ActiveSonar.java

Active sonar sense.
"""

from kirby_cost.objects.powers.sense import Sense


class ActiveSonar(Sense, xmlid="ACTIVESONAR"):
    """
    Active Sonar power.
    
    Sense for active sonar detection.
    """
    
    def __init__(self):
        """Initialize an Active Sonar power."""
        super().__init__(ActiveSonar.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Active Sonar)."""
        return ""

