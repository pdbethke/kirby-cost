"""
Tunneling power class for kirby-cost.

Converted from com.hero.objects.powers.Tunneling.java

Power to tunnel through materials.
"""

from kirby_cost.objects.powers.power import Power


class Tunneling(Power, xmlid="TUNNELING"):
    """
    Tunneling power.
    
    Power to tunnel through materials.
    """
    
    def __init__(self):
        """Initialize a Tunneling power."""
        super().__init__()
        self.xmlid = Tunneling.XMLID
        self.affects_primary = True
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """``12m through 10 PD material``.

        Ported from ``Tunneling.getDamageDisplay`` (6E branch). The defence
        starts at 1 — everything can be tunnelled through something — and
        DEFBONUS adds to it. Omitting the defence left "12m through material",
        which does not say what the tunnelling is good for.
        """
        defence = 1
        for ad in self.assigned_adders:
            if ad.xmlid == "DEFBONUS":
                defence += ad.levels
        return f"{self._levels}m through {defence} PD material"
    @property
    def column2_output(self) -> str:
        """``Tunneling 12m through 10 PD material, Fill In``.

        Ported from ``Tunneling.getColumn2Output``. The DEFBONUS adder is
        pulled OUT of the adder list before it is rendered, because the
        defence it buys is already part of what the tunnelling goes through —
        listing it again would say the same thing twice.
        """
        from kirby_cost.objects.base import option_alias
        ret = f"{self.alias or ''} {self.damage_display}"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self.input and self.input.strip():
            ret += f":  {self.input}"

        original = self._assigned_adders
        self._assigned_adders = [a for a in original if a.xmlid != "DEFBONUS"]
        try:
            adders = self.adder_string
        finally:
            self._assigned_adders = original

        option = (option_alias(self) or "").strip()
        if option:
            ret += " (" + option
            if adders.strip():
                ret += "; " + adders
            ret += ")"
        elif adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
