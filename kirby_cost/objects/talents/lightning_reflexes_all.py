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
        """
        Get formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        # Check if 6E template
        from kirby_cost.core.template import Template
        template = EngineContext.active_template()
        if template and template.is_6e():
            output = self._alias
            
            # Add name if present
            if self._name and self._name.strip():
                output = f"<i>{self._name}:</i>  {output}"
            
            # Add selected option
            if self._selected_option:
                output = output + " (+"
                output = output + str(self._levels) + " DEX to act first with "
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
        
        return super().column2_output



