"""
WeaponFamiliarity skill class for kirby-cost.

Converted from com.hero.objects.skills.WeaponFamiliarity.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import characteristic_string

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class WeaponFamiliarity(Skill, xmlid="WEAPON_FAMILIARITY"):
    """Weapon Familiarity skill."""
    
    _roll_based_default = False
    
    def __init__(self, xmlid: str = None):
        """Initialize WeaponFamiliarity."""
        super().__init__(xmlid or WeaponFamiliarity.XMLID)
        self._alias = "WF"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        string3 = self._alias
        
        if self.input and self.input.strip():
            string3 = f"{string3}:  {self.input}"
        
        # Characteristic-based note (stub - would need HeroDesigner.getInstance().getPrefs().useWG() check)
        if (self.characteristic_choices and 
            len(self.characteristic_choices) > 1 and 
            self.characteristic != 0):
            string3 = f"{string3} ({characteristic_string(self.characteristic)}-based)"
        
        adder_str = self.adder_string
        if adder_str.strip():
            string3 = f"{string3}:  {adder_str}"
        
        modifier_str = self.modifier_string
        if modifier_str.strip():
            string3 = f"{string3} {modifier_str}"
        
        # END Reserve note (stub)
        # if (self.get_end_usage() > 0 and ...):
        #     ...
        
        return string3
    
    @property
    def roll(self) -> str:
        """Get roll (empty for weapon familiarity)."""
        return ""
    
    

