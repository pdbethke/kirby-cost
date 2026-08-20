"""
Microscopic power class for kirby-cost.

Converted from com.hero.objects.powers.Microscopic.java

Microscopic sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder
import math


class Microscopic(SenseAdder, xmlid="MICROSCOPIC"):
    """
    Microscopic power.
    
    Sense adder that provides microscopic vision.
    """
    
    def __init__(self):
        """Initialize a Microscopic power."""
        super().__init__(Microscopic.XMLID)
        self._duration = "CONSTANT"
        # Stub: would auto-select first option if available
    
    @property
    def damage_display(self) -> str:
        """Get microscopic display."""
        multiplier = int(math.pow(self.level_power, self._levels))
        return f" x{multiplier:,}"
    
    @property
    def column2_output(self) -> str:
        """``Microscopic ( x100) with Sight Group``.

        Ported from ``Microscopic.getColumn2Output``. Magnification without a
        sense is meaningless — x100 of WHAT — and the sense is the object's
        selected option, which this dropped.
        """
        from kirby_cost.objects.base import option_alias
        ret = f"{self.alias or ''} ({self.damage_display})"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"

        with_str = " with "
        option = (option_alias(self) or "").strip()
        adders = self.adder_string or ""
        if option:
            with_str += option
            if adders.strip():
                with_str += ", " + adders
                i = with_str.rfind(",")
                with_str = with_str[:i] + " and" + with_str[i + 1:]
        elif adders.strip():
            with_str += " " + adders
            if ", " in with_str:
                i = with_str.rfind(",")
                with_str = with_str[:i] + " and" + with_str[i + 1:]
        ret += with_str
        ret += self.modifier_string
        return ret
