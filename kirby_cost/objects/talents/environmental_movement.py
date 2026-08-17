"""
Environmental Movement Talent for kirby-cost.

Converted from com.hero.objects.talents.EnvironmentalMovement.java

Environmental Movement allows movement in specific environments.
"""

from typing import Optional
from kirby_cost.objects.talents.talent import Talent
from kirby_cost.objects.base import GenericObject
from kirby_cost.core.context import EngineContext


class EnvironmentalMovement(Talent, xmlid="ENVIRONMENTAL_MOVEMENT"):
    """
    Environmental Movement Talent.
    
    Allows movement in specific environments.
    """
    
    def __init__(self, element=None):
        """Initialize an Environmental Movement talent."""
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
        
        # Add input in parentheses
        if self.input and self.input.strip():
            output = output + " (" + self.input + ")"
        
        # Add selected option and adders
        if self._selected_option:
            output = output + " ("
            output = output + self._selected_option.alias
            adder_str = self.adder_string
            if adder_str.strip():
                output = output + "; " + adder_str
            output = output + ")"
        else:
            adder_str = self.adder_string
            if adder_str.strip():
                output = output + " (" + adder_str + ")"
        
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
                    all_mods = self.assigned_modifiers
                    end_reserve_mod = GenericObject.find_object_by_id(all_mods, "ENDRESERVEOREND")
                    prefs = EngineContext.prefs()
                    if not end_reserve_mod and not prefs.use_wg:
                        if self._use_end_reserve:
                            output = output + " (uses END Reserve)"
                        else:
                            output = output + " (uses Personal END)"
        
        return output



