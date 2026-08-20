"""
Fringe Benefit Perk for kirby-cost.

Converted from com.hero.objects.perks.FringeBenefit.java

Fringe Benefit represents employment or organizational benefits.
"""

from typing import Optional
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.objects.base import GenericObject
from kirby_cost.core.context import EngineContext


class FringeBenefit(Perk, xmlid="FRINGE_BENEFIT"):
    """
    Fringe Benefit Perk.
    
    Represents employment or organizational benefits.
    """
    
    def __init__(self, element=None):
        """Initialize a Fringe Benefit perk."""
        super().__init__(element, self.XMLID)
    
    @property
    def column2_output(self) -> str:
        """``Fringe Benefit:  Local Police Powers``.

        Ported from ``FringeBenefit.getColumn2Output``. The option is joined
        with ":  " rather than brackets — a fringe benefit IS its option; the
        alias is only a heading — and the roll, where the benefit has one,
        comes after the modifiers rather than before them.
        """
        from kirby_cost.objects.base import option_alias
        ret = self.alias or ""
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        option = (option_alias(self) or "").strip()
        adders = self.adder_string
        if option:
            ret += f":  {option}"
            if adders.strip():
                ret += f"; {adders}"
        elif adders.strip():
            ret += f":  {adders}"
        ret += self.modifier_string
        roll = (getattr(self, "roll", "") or "").strip()
        if roll:
            ret += f" {roll}"
        return ret
