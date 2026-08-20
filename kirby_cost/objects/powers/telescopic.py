"""
Telescopic power class for kirby-cost.

Converted from com.hero.objects.powers.Telescopic.java

Telescopic sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class Telescopic(SenseAdder, xmlid="TELESCOPIC"):
    """
    Telescopic power.
    
    Sense adder that provides range modifier bonuses.
    """
    
    def __init__(self):
        """Initialize a Telescopic power."""
        super().__init__(Telescopic.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get telescopic display."""
        return f" +{self._levels} versus Range Modifier"
    
    @property
    def column2_output(self) -> str:
        """``+4 versus Range Modifier for Sight Group``.

        Ported from ``Telescopic.getColumn2Output``. It does not name itself
        at all — the alias never appears — and it joins its sense with "for"
        where the other sense adders use "with".
        """
        from kirby_cost.objects.base import option_alias
        ret = f"+{self._levels} versus Range Modifier"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"

        with_str = " for "
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
