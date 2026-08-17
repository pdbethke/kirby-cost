"""
Resistance Talent for kirby-cost.

Converted from com.hero.objects.talents.Resistance.java

Resistance provides bonuses to resistance rolls.
"""

from typing import Optional
from kirby_cost.objects.talents.talent import Talent


class Resistance(Talent, xmlid="RESISTANCE"):
    """
    Resistance Talent.

    Provides bonuses to resistance rolls.
    """

    def __init__(self, element=None):
        """Initialize a Resistance talent."""
        super().__init__(element, self.XMLID)
        self.set_levels(self._levels)

    def set_levels(self, levels: int) -> None:
        """
        Set levels and update alias.

        Args:
            levels: Number of levels
        """
        # Check if alias matches display (needs update)
        needs_update = False
        if self._alias == self._display:
            needs_update = True
        elif self._alias == f"{self._display} (+{self._levels} to roll)":
            needs_update = True

        self._levels = levels

        if needs_update:
            self._alias = f"{self._display} (+{self._levels} to roll)"
