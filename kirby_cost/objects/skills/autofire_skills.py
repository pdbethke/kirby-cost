"""
AutofireSkills skill class for kirby-cost.

Converted from com.hero.objects.skills.AutofireSkills.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import characteristic_string

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type


class AutofireSkills(Skill, xmlid="AUTOFIRE_SKILLS"):
    """Autofire Skills."""
    
    _roll_based_default = False
    
    def __init__(self, xmlid: str = None):
        """Initialize AutofireSkills."""
        super().__init__(xmlid or AutofireSkills.XMLID)
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        active_hero = self._get_active_hero()
        
        string2 = self._selected_option.alias if self._selected_option is not None else ""
        
        if self._name and self._name.strip():
            string2 = f"<i>{self._name}:</i>  {string2}"
        
        if self.input and self.input.strip():
            string2 = f"{string2}:  {self.input}"
        
        # Characteristic-based note (stub - would need HeroDesigner.getInstance().getPrefs().useWG() check)
        if (self.characteristic_choices and 
            len(self.characteristic_choices) > 1 and 
            self.characteristic != 0):
            string2 = f"{string2} ({characteristic_string(self.characteristic)}-based)"
        
        adder_str = self.adder_string
        if adder_str.strip():
            string2 = f"{string2} ({adder_str})"
        
        string2 = string2 + self.modifier_string
        
        # END Reserve note (stub - would need END Reserve check and useWG() check)
        # if (self.get_end_usage() > 0 and ...):
        #     string2 = f"{string2} ({'uses END Reserve' if self.use_end_reserve else 'uses Personal END'})"
        
        return string2
    
    



