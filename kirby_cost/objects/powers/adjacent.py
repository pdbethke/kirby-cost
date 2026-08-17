"""
Adjacent power class for kirby-cost.

Converted from com.hero.objects.powers.Adjacent.java

Adjacent sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class Adjacent(SenseAdder, xmlid="ADJACENT"):
    """
    Adjacent power.
    
    Sense adder for adjacent range.
    """
    
    def __init__(self):
        """Initialize an Adjacent power."""
        super().__init__(Adjacent.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Adjacent)."""
        return ""

