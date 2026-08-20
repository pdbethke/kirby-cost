"""
Lightning Reflexes (All Actions) Talent for kirby-cost.

Converted from com.hero.objects.talents.LightningReflexesAll.java

Lightning Reflexes provides bonuses to act first with all actions.
"""

from typing import Optional
from kirby_cost.objects.talents.talent import Talent
from kirby_cost.objects.base import GenericObject
from kirby_cost.core.context import EngineContext


class LightningReflexesAll(Talent, xmlid="LIGHTNING_REFLEXES_ALL"):
    """
    Lightning Reflexes (All Actions) Talent.
    
    Provides bonuses to act first with all actions.
    """
    
    def __init__(self, element=None):
        """Initialize a Lightning Reflexes (All Actions) talent."""
        super().__init__(element, self.XMLID)
        self._levels = self._levels
    
    @property
    def levels(self) -> int:
        """Get the number of levels."""
        return self._levels

    @levels.setter
    def levels(self, levels: int) -> None:
        """
        Set levels and update alias.

        Args:
            levels: Number of levels
        """
        self._levels = levels

        # Update alias if display contains "All Actions"
        display = self._display
        if "All Actions" in display:
            idx = display.index("All Actions")
            prefix = display[:idx]
            suffix = display[idx:]
            self._alias = f"{prefix}+{self._levels} DEX to act first with {suffix}"
    
    @property
    def column2_output(self) -> str:
        """``Lightning Reflexes (+10 DEX to act first with Spirit Travel)``.

        Ported from ``LightningReflexesAll.getColumn2Output`` (6E branch). The
        bracket is a sentence, not a list: it says how much DEX and what for.
        Printing the option alone — "Lightning Reflexes (Spirit Travel)" — drops
        the number the talent is bought for.
        """
        from kirby_cost.objects.base import option_alias
        ret = self.alias or ""
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        option = (option_alias(self) or "").strip()
        adders = self.adder_string
        if option:
            ret += f" (+{self._levels} DEX to act first with {option}"
            if adders.strip():
                ret += f"; {adders}"
            ret += ")"
        elif adders.strip():
            ret += f" ({adders})"
        ret += self.modifier_string
        return ret
