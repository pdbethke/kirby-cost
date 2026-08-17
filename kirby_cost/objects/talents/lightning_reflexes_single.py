"""
Lightning Reflexes (Single Action) Talent for kirby-cost.

Converted from com.hero.objects.talents.LightningReflexesSingle.java

Lightning Reflexes provides bonuses to act first with a single action.
"""

from typing import Optional
from kirby_cost.objects.talents.talent import Talent
from kirby_cost.objects.base import GenericObject
from kirby_cost.core.context import EngineContext


class LightningReflexesSingle(Talent, xmlid="LIGHTNING_REFLEXES_SINGLE"):
    """
    Lightning Reflexes (Single Action) Talent.
    
    Provides bonuses to act first with a single action.
    """
    
    def __init__(self, element=None):
        """Initialize a Lightning Reflexes (Single Action) talent."""
        super().__init__(element, self.XMLID)
        self.input("Single Action")
    
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
        
        # Add selected option
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
    
    def input(self, input_str: str) -> None:
        """
        Set input and update alias.
        
        Args:
            input_str: Input string to set
        """
        super().input(input_str)
        
        # Update alias if display contains "Single Action"
        display = self._display
        if "Single Action" in display:
            idx = display.index("Single Action")
            prefix = display[:idx]
            suffix_start = idx + len("Single Action")
            if suffix_start < len(display):
                suffix = display[suffix_start:]
            else:
                suffix = ""
            self._alias = f"{prefix}+{self._levels} DEX to act first with {input_str}{suffix}"
    
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
        alias = self._alias
        level_str = f"+{self._levels}"
        if level_str in alias:
            idx = alias.index(level_str)
            prefix = alias[:idx]
            # Find end of level number
            level_end = idx + len(level_str)
            if self._levels < 10:
                level_end += 1  # Account for space or next char
            else:
                level_end += 2
            if level_end < len(alias):
                suffix = alias[level_end:]
            else:
                suffix = ""
            self._levels = levels
            self._alias = f"{prefix}+{self._levels}{suffix}"
        else:
            self._levels = levels



