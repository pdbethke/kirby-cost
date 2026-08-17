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
        """
        Get formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        output = self._alias
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add input
        if self.input and self.input.strip():
            output = output + ":  " + self.input
        
        # Add selected option and adders
        if self._selected_option:
            output = output + ":  "
            output = output + self._selected_option.alias
            adder_str = self.adder_string
            if adder_str.strip():
                output = output + "; " + adder_str
        else:
            adder_str = self.adder_string
            if adder_str.strip():
                output = output + ":  " + adder_str
        
        # Add modifiers
        output = output + self.modifier_string
        
        # Add roll if present
        roll = self.roll
        if roll and roll.strip():
            output = output + " " + roll
        
        # Add END usage note
        if self.end_usage > 0:
            active_hero = EngineContext.active_hero()
            if active_hero:
                end_reserve = GenericObject.find_object_by_id(active_hero.powers, "ENDURANCERESERVE")
                if end_reserve:
                    all_mods = self.all_assigned_modifiers
                    end_reserve_mod = GenericObject.find_object_by_id(all_mods, "ENDRESERVEOREND")
                    prefs = EngineContext.prefs()
                    if not end_reserve_mod and not prefs.use_wg:
                        if self._use_end_reserve:
                            output = output + " (uses END Reserve)"
                        else:
                            output = output + " (uses Personal END)"
        
        return output



