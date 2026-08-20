"""
Flash power class for kirby-cost.

Converted from com.hero.objects.powers.Flash.java

Flash blinds sense groups.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class Flash(SenseAffectingPower, xmlid="FLASH"):
    """
    Flash power.
    
    Blinds specified sense groups.
    """
    
    def __init__(self):
        """Initialize a Flash power."""
        super().__init__()
        self.xmlid = Flash.XMLID
        self._duration = "INSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get flash display string."""
        return f"{self._levels}d6"
    
    @property
    def column2_output(self) -> str:
        """``Sight Group Flash 4d6`` — what it affects, then what it is.

        Ported from ``Flash.getColumn2Output``. All three sense-affecting
        powers open with the groups and senses they act on and only then name
        themselves; this printed the alias first and the group last, which is
        the same words in the wrong order.
        """
        ret = self._sense_prefix()
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        ret += " " + (self.alias or "")
        ret += " " + self.damage_display
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
