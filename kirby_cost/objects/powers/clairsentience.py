"""
Clairsentience power class for kirby-cost.

Converted from com.hero.objects.powers.Clairsentience.java

Power for remote sensing.
"""

from kirby_cost.util.rounder import round_half_up
from kirby_cost.objects.powers.sense_affecting_power import sense_prefix
from kirby_cost.objects.powers.power import Power


class Clairsentience(Power, xmlid="CLAIRSENTIENCE"):
    """
    Clairsentience power.
    
    Power for remote sensing at a distance.
    """
    
    def __init__(self):
        """Initialize a Clairsentience power."""
        super().__init__()
        self.xmlid = Clairsentience.XMLID
        self._duration = "CONSTANT"
        self.nontargeting_group_cost: float = 0.0
        self.nontargeting_sense_cost: float = 0.0
        self.targeting_group_cost: float = 0.0
        self.targeting_sense_cost: float = 0.0
        self.old_method: bool = False
    
    @property
    def damage_display(self) -> str:
        """Get clairsentience display."""
        return f"{self._levels}m range"
    
    @property
    def assigned_adders(self):
        """
        Get assigned adders with special handling.
        
        Removes CONCEALED if TRANSMIT not present.
        Removes ANALYZESENSE if DISCRIMINATORY present.
        """
        adders = super().assigned_adders
        
        # Stub: would filter adders based on special rules
        # For now, return as-is
        return adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value

    def _increased_range(self, adder) -> int:
        """How far the power sees once INCREASEDRANGE is bought.

        Ported from ``Clairsentience.getRangeValue``. Java computes the base
        range with the adder temporarily removed, then multiplies — the adder
        is a MULTIPLIER on the range, not an addition to it, and reading the
        range with the adder still in place would count it twice.
        """
        original = self._assigned_adders
        self._assigned_adders = [a for a in original if a is not adder]
        try:
            base = self.range_value
        finally:
            self._assigned_adders = original
        if base <= 0:
            return int(base)
        power = adder._level_power_for_display
        return int(round_half_up(base * (power ** adder.levels)))

    @property
    def column2_output(self) -> str:
        """``Precognitive Clairsentience (Sight Group)``.

        Ported from ``Clairsentience.getColumn2Output``. Seeing across TIME is
        not an adder to be listed after the power — it changes what the power
        IS, so PERCEIVEPAST and PERCEIVEFUTURE are lifted out and put in front
        of the alias as "Retrocognitive" and "Precognitive". A power that does
        both reads "Retrocognitive, Precognitive Clairsentience".

        INCREASEDRANGE becomes a distance rather than a count, and the range
        the power has without it is not printed at all — "0m range" was a
        measurement HD does not make.
        """
        from kirby_cost.objects.base import option_alias
        ret = self.alias or ""
        prefixed = False
        adder_str = ""

        for ad in list(self.assigned_adders):
            if ad.xmlid == "INCREASEDRANGE":
                ad.display_in_string = False
                if adder_str:
                    adder_str += ", "
                adder_str += (f"{ad.alias or ''} "
                              f"({self._increased_range(ad):,}m)")
            elif ad.xmlid in ("PERCEIVEPAST", "PERCEIVEFUTURE"):
                ad.display_in_string = False
                word = ("Retrocognitive" if ad.xmlid == "PERCEIVEPAST"
                        else "Precognitive")
                ret = f"{word}{',' if prefixed else ''} {ret}"
                prefixed = True

        prefix = sense_prefix(self, "[Unknown]", joiner=" And ")
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        ret += " (" + prefix + ")"
        if self.input and self.input.strip():
            ret += f":  {self.input}"

        ads = self.adder_string
        if ads.strip():
            if adder_str.strip():
                adder_str += ", "
            adder_str += ads
        if adder_str.strip():
            ret += ", " + adder_str
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
