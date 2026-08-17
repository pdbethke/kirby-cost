"""
MentalCombatLevels skill class for kirby-cost.

Converted from com.hero.objects.skills.MentalCombatLevels.java
"""

from kirby_cost.objects.skills.skill import Skill
from kirby_cost.util.constants import characteristic_string


class MentalCombatLevels(Skill, xmlid="MENTAL_COMBAT_LEVELS"):
    """Mental Combat Levels skill."""
    
    XML_ID = "MENTAL_COMBAT_LEVELS"
    
    def __init__(self, xmlid: str = None):
        """Initialize MentalCombatLevels."""
        super().__init__(xmlid or MentalCombatLevels.XML_ID)
        # 6E1 p73: "For 1 Character Point, a character can buy +1" (MCSLs).
        # Skill.__init__ sets the generic 2.0, which is wrong here.
        self._level_cost = 1.0
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        string2 = f"{'+' if self._levels >= 0 else ''}{self._levels} {self._selected_option.alias}"
        
        if self._name and self._name.strip():
            string2 = f"<i>{self._name}:</i>  {string2}"
        
        if self.input and self.input.strip():
            string2 = f"{string2}:  {self.input}"
        
        # Characteristic-based note (stub)
        if (self.characteristic_choices and 
            len(self.characteristic_choices) > 1 and 
            self.characteristic != 0):
            string2 = f"{string2} ({characteristic_string(self.characteristic)}-based)"
        
        adder_str = self.adder_string
        if adder_str.strip():
            string2 = f"{string2} ({adder_str})"
        
        string2 = f"{string2}{self.modifier_string}"
        
        return string2
    
    @property
    def roll(self) -> str:
        """Get roll (empty for mental combat levels)."""
        return ""
    
    




