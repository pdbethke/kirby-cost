"""
Summon power class for kirby-cost.

Converted from com.hero.objects.powers.Summon.java

Power to summon beings.
"""

from kirby_cost.objects.powers.power import Power
from pathlib import Path
from typing import Optional


class Summon(Power, xmlid="SUMMON"):
    """
    Summon power.
    
    Summons beings to serve the character.
    """
    
    def __init__(self):
        """Initialize a Summon power."""
        super().__init__()
        self.xmlid = Summon.XMLID
        self._duration = "INSTANT"
        self.file_path: Optional[str] = None
        self.file_association_last_check: Optional[int] = None
    
    @property
    def damage_display(self) -> str:
        """Get summon display."""
        # Calculate total from base and INCREASETOTAL adder
        total = 1.0
        for adder in self.assigned_adders:
            if adder.xmlid == "INCREASETOTAL":
                adder.display_in_string = False
                total += adder.levels * adder.level_multiplier
        
        return f"{int(total)}x {self.input or 'Base Points'}"
    
    def clear_file_path(self) -> None:
        """Clear associated file path."""
        self.file_path = None
        self.file_association_last_check = None

    @property
    def column2_output(self) -> str:
        """``Summon 298-point Treeman``.

        Ported from ``Summon.getColumn2Output``. What is summoned is measured
        in POINTS — the levels are the creature's point total, not a die count
        — and the INCREASETOTAL adder says how many, which is why it is marked
        not-to-be-printed once read. With no input HD says "creatures".
        """
        from kirby_cost.objects.base import option_alias
        ret = self.alias or ""
        number = 1
        for ad in self.assigned_adders:
            if ad.xmlid == "INCREASETOTAL":
                ad.display_in_string = False
                power = ad._level_power_for_display
                if power <= 1:
                    number = ad.levels * ad.level_multiplier
                else:
                    number = ad.level_multiplier * (power ** ad.levels)
        if number > 1:
            ret += f" {int(number)}"
        ret += f" {self._levels}-point"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self.input and self.input.strip():
            ret += f" {self.input}"
        else:
            ret += " creatures"
        option = (option_alias(self) or "").strip()
        adders = self.adder_string
        if option:
            ret += f" ({option}"
            if adders.strip():
                ret += f"; {adders}"
            ret += ")"
        elif adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
