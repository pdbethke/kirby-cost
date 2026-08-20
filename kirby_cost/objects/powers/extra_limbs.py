"""
Extra Limbs power class for kirby-cost.

Converted from com.hero.objects.powers.ExtraLimbs.java

Power to have extra limbs.
"""

from kirby_cost.objects.base import option_alias
from kirby_cost.objects.powers.power import Power


class ExtraLimbs(Power, xmlid="EXTRALIMBS"):
    """
    Extra Limbs power.
    
    Provides additional limbs.
    """
    
    def __init__(self):
        """Initialize an Extra Limbs power."""
        super().__init__()
        self.xmlid = ExtraLimbs.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Extra Limbs)."""
        return ""
    
    @property
    def column2_output(self) -> str:
        """``Extra Limb (1)`` for one, ``Extra Limbs (4)`` for more.

        Ported from ``ExtraLimbs.getColumn2Output``. Two details this missed:
        HD trims before appending the count, so "Extra Limbs  (1)" had a
        doubled space where the empty damage display used to be; and at
        exactly one limb it drops a trailing "S" from whatever the line
        currently says, which makes the alias singular without needing a
        second name for it.
        """
        ret = f"{self.alias or ''} {self.damage_display}"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self._levels == 1:
            ret = ret.strip()
            if ret.upper().endswith("S"):
                ret = ret[:-1]
        if self._levels > 0:
            # No trim: HD leaves the space where the empty damage
            # display was, so "Extra Limbs  (2)" has two.
            ret += f" ({self._levels})"
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        option = (option_alias(self) or "").strip()
        if option:
            ret += f" ({option})"
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
