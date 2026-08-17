"""
Telekinesis power class for kirby-cost.

Converted from com.hero.objects.powers.Telekinesis.java

Telekinesis allows mental manipulation of objects.
"""

from kirby_cost.objects.powers.power import Power


class Telekinesis(Power, xmlid="TELEKINESIS"):
    """
    Telekinesis power.
    
    Allows mental manipulation of objects with STR equivalent.
    """
    
    def __init__(self):
        """Initialize a Telekinesis power."""
        super().__init__()
        self.xmlid = Telekinesis.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get STR equivalent display."""
        return f"({self._levels} STR)"

