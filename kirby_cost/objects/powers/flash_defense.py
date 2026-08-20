"""
Flash Defense power class for kirby-cost.

Converted from com.hero.objects.powers.FlashDefense.java

Defense against flash attacks.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class FlashDefense(SenseAffectingPower, xmlid="FLASHDEFENSE"):
    """
    Flash Defense power.
    
    Defense against flash attacks (sense-affecting).
    """
    
    def __init__(self):
        """Initialize a Flash Defense power."""
        super().__init__()
        self.xmlid = FlashDefense.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """``(10 points)`` — and nothing at all for a single point.

        Ported from ``FlashDefense.getDamageDisplay``. The brackets belong to
        the power rather than to an adder list, the number is levels divided
        by the level value rather than the raw levels, and one point prints as
        no number at all: "Sight Group Flash Defense" says everything there is
        to say.
        """
        from kirby_cost.util.rounder import round_down
        num = int(round_down(self._levels / (self._level_value or 1.0)))
        return f"({num} points)" if num > 1 else ""
    
    @property
    def column2_output(self) -> str:
        """``Sight Group Flash 4d6`` — what it affects, then what it is.

        Ported from ``FlashDefense.getColumn2Output``. All three sense-affecting
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
