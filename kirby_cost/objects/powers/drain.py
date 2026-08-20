"""
Drain power class for kirby-cost.

Converted from com.hero.objects.powers.Drain.java

Drain reduces characteristics temporarily.
"""

from kirby_cost.objects.powers.power import Power


class Drain(Power, xmlid="DRAIN"):
    """
    Drain power.
    
    Reduces characteristics temporarily (or Suppress in 6E with COSTENDTOMAINTAIN).
    """
    
    def __init__(self):
        """Initialize a Drain power."""
        super().__init__()
        self.xmlid = Drain.XMLID
        self._duration = "INSTANT"
    
    @property
    def alias(self) -> str:
        """Get alias (Drain or Suppress in 6E)."""
        # Stub: would check if 6E and has COSTENDTOMAINTAIN modifier
        # For now, return base alias
        return self._alias or "Drain"
    
    @property
    def damage_display(self) -> str:
        """Power's, unchanged — Drain.java has no getDamageDisplay of its own.

        The override here returned a bare "{levels}d6", which loses the pip
        adders: a Drain of no levels with a PLUSONEPIP reads "1 point" in HD,
        not "0d6".
        """
        return super().damage_display
    
    @property
    def column2_output(self) -> str:
        """``Drain STR 3d6``.

        Ported from ``Drain.getColumn2Output``. What is drained is the INPUT
        and it goes between the alias and the dice — "Drain STR 3d6", not
        "Drain 3d6:  STR" — because the sentence names the thing being taken
        before it says how much.
        """
        from kirby_cost.objects.base import option_alias
        ret = self.alias or ""
        if self.input and self.input.strip():
            ret += f" {self.input}"
        ret += f" {self.damage_display}"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        option = (option_alias(self) or "").strip()
        if option:
            ret += f" ({option})"
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
