"""
Talent base class for kirby-cost.

Converted from com.hero.objects.talents.Talent.java

Talents are innate abilities.
"""

from typing import Optional
from kirby_cost.objects.base import GenericObject
from kirby_cost.core.context import EngineContext
from kirby_cost.io.xml_utility import XMLUtility


class Talent(GenericObject):
    """
    Base class for all Talents.
    
    Talents are innate abilities like Combat Luck, Danger Sense, etc.
    """
    
    def __init__(self, element=None, xmlid: Optional[str] = None):
        """
        Initialize a Talent.
        
        Args:
            element: Optional XML element for initialization
            xmlid: Optional XMLID to set
        """
        super().__init__()
        if xmlid:
            self.xmlid = xmlid
        
        if element is not None:
            self._init(element)
    
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
    
    @property
    def roll(self) -> str:
        """
        Get roll value for this talent (if applicable).
        
        Returns:
            Roll string or empty string
        """
        return ""
    
    def get_save_xml(self):
        """Get XML element for saving."""
        element = super().get_save_xml()
        element.tag = "TALENT"
        return element
    
    def _init(self, element) -> None:
        """Initialize from XML element."""
        self._duration = "CONSTANT"
        super()._init(element)
        self.target = "SELFONLY"
        
        if "SPECIAL" not in self._types:
            self._types.append("SPECIAL")
        
        target_val = XMLUtility.get_value(element, "TARGET")
        if target_val and target_val.strip():
            self.target = target_val



