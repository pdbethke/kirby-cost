"""
Discriminatory Sense power class for kirby-cost.

Converted from com.hero.objects.powers.DiscriminatorySense.java

Discriminatory sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class DiscriminatorySense(SenseAdder, xmlid="DISCRIMINATORY"):
    """
    Discriminatory Sense power.
    
    Sense adder that provides discriminatory ability.
    """
    
    def __init__(self):
        """Initialize a Discriminatory Sense power."""
        super().__init__(DiscriminatorySense.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Discriminatory Sense)."""
        return ""

