"""
DefenseManeuver skill class for kirby-cost.

Converted from com.hero.objects.skills.DefenseManeuver.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import characteristic_string

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type


class DefenseManeuver(Skill, xmlid="DEFENSE_MANEUVER"):
    """Defense Maneuver skill."""
    
    _roll_based_default = False
    
    def __init__(self, xmlid: str = None):
        """Initialize DefenseManeuver."""
        super().__init__(xmlid or DefenseManeuver.XMLID)
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        string2 = self._alias
        
        if self._name and self._name.strip():
            string2 = f"<i>{self._name}:</i>  {string2}"
        
        if self.input and self.input.strip():
            string2 = f"{string2}:  {self.input}"
        
        if self._selected_option is not None:
            string2 = f"{string2} {self._selected_option.alias}"
        
        # Characteristic-based note (stub - would need HeroDesigner.getInstance().getPrefs().useWG() check)
        if (self.characteristic_choices and 
            len(self.characteristic_choices) > 1 and 
            self.characteristic != 0):
            string2 = f"{string2} ({characteristic_string(self.characteristic)}-based)"
        
        adder_str = self.adder_string
        if adder_str.strip():
            string2 = f"{string2} ({adder_str})"
        
        string2 = f"{string2}{self.modifier_string}"
        string2 = f"{string2} {self.roll}"
        
        # END Reserve note (stub)
        # if (self.get_end_usage() > 0 and ...):
        #     ...
        
        return string2
    
    @property
    def roll(self) -> str:
        """Get roll (empty for defense maneuver)."""
        return ""
    
    def get_save_xml(self) -> 'Element':
        """Get save XML."""
        element = super().get_save_xml()
        element.attrib.pop("CHARACTERISTIC", None)
        return element
    
    



