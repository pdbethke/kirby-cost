"""
Luck power class for kirby-cost.

Converted from com.hero.objects.powers.Luck.java

Luck power.
"""

from kirby_cost.objects.powers.power import Power


class Luck(Power, xmlid="LUCK"):
    """
    Luck power.
    
    Provides luck points for rerolls and other effects.
    """
    
    def __init__(self):
        """Initialize a Luck power."""
        super().__init__()
        self.xmlid = Luck.XMLID
        self._duration = "CONSTANT"

