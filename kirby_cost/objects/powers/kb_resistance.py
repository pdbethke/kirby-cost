"""
Knockback Resistance power class for kirby-cost.

Converted from com.hero.objects.powers.KBResistance.java

Resistance to knockback.
"""

from kirby_cost.objects.powers.power import Power


class KBResistance(Power, xmlid="KBRESISTANCE"):
    """
    Knockback Resistance power.
    
    Reduces knockback taken.
    """
    
    def __init__(self):
        """Initialize a Knockback Resistance power."""
        super().__init__()
        self.xmlid = KBResistance.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get KB resistance display."""
        is_6e = True  # Stub: would check if 6E
        return f"-{self._levels}m" if is_6e else f'-{self._levels}"'

