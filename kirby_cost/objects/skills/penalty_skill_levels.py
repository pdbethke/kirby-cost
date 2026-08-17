"""
PenaltySkillLevels skill class for kirby-cost.

Converted from com.hero.objects.skills.PenaltySkillLevels.java
"""

from kirby_cost.objects.skills.skill import Skill
from kirby_cost.util.constants import characteristic_string


class PenaltySkillLevels(Skill, xmlid="PENALTY_SKILL_LEVELS"):
    """Penalty Skill Levels skill."""
    
    XML_ID = "PENALTY_SKILL_LEVELS"
    
    def __init__(self, xmlid: str = None):
        """Initialize PenaltySkillLevels."""
        super().__init__(xmlid or PenaltySkillLevels.XML_ID)
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        # Check if we should use old format
        if (self._selected_option and 
            (self._selected_option.display.startswith("vs.") or
             self._selected_option.display.startswith("with") or
             not self.input or not self.input.strip())):
            return self._get_old_column2_output()
        
        # New format
        string2 = f"{self._alias}:  "
        string2 = f"{string2}{'+' if self._levels >= 0 else ''}{self._levels} vs. {self.input} with {self._selected_option.alias}"
        
        if self._name and self._name.strip():
            string2 = f"<i>{self._name}:</i>  {string2}"
        
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
    
    def _get_old_column2_output(self) -> str:
        """Get old column 2 output format."""
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
        """Get roll (empty for penalty skill levels)."""
        return ""
    
    




