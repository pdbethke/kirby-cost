"""
ProfessionalSkill skill class for kirby-cost.

Converted from com.hero.objects.skills.ProfessionalSkill.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import characteristic_string
from kirby_cost.util.rounder import round_half_up

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class ProfessionalSkill(Skill, xmlid="PROFESSIONAL_SKILL"):
    """Professional Skill."""
    
    def __init__(self, xmlid: str = None):
        """Initialize ProfessionalSkill."""
        super().__init__(xmlid or ProfessionalSkill.XMLID)
        self._alias = "PS"
        # 6E1 p88: "+1 to roll per +1 point". Background Skills cost 1 CP
        # per +1; Skill.__init__ sets the generic 2.0 (6E1 p63 -- most
        # Skills are "3/2"), which is wrong for this family. Knowledge
        # Skill already overrides it; this was its missed neighbour.
        self._level_cost = 1.0
    
    def roll_value(self, active_hero: Optional['Hero'] = None) -> int:
        """Get roll value."""
        if active_hero is None:
            active_hero = self._get_active_hero()
        
        n = 0
        if self.is_familiarity:
            n = 11 if self.is_everyman else (self.familiarity_roll if self.familiarity_roll > 0 else 8)
        elif self.is_proficiency:
            n = self.proficiency_roll if self.proficiency_roll > 0 else 10
        elif self._is_focus() and active_hero is not None:
            n = active_hero.rules.skill_roll_base
            n = self._minimum_level if self._levels < 0 else (n + self._levels)
        elif active_hero is not None:
            char = active_hero.characteristic(self.characteristic)
            n3 = active_hero.rules.skill_roll_base
            
            if char is not None and char.xmlid != "GENERAL":
                n3 = (active_hero.rules.skill_roll_base + 
                      int(round_half_up(char.get_primary_value(active_hero) / active_hero.rules.skill_roll_denominator) + 
                          float(self._levels) * self._level_value))
            elif self.characteristic == 0:
                # Would need HeroDesigner.getActiveTemplate().getGeneralLevel()
                # For now, use rules.get_general_level() if available
                general_level = active_hero.rules.general_level if hasattr(active_hero.rules, 'general_level') else 10
                n3 = (active_hero.rules.skill_roll_base + 
                      int(round_half_up(float(general_level) / active_hero.rules.skill_roll_denominator) + 
                          float(self._levels) * self._level_value))
            else:
                n3 = (active_hero.rules.skill_roll_base + 
                      int(round_half_up(float(self._levels) * self._level_value)))
            n = n3
        else:
            # Fallback when no active hero
            # Would need HeroDesigner.getActiveTemplate().getGeneralLevel()
            general_level = 10  # Default fallback
            n = 9 + int(round_half_up(float(general_level) / 5.0) + float(self._levels) * self._level_value)
        
        return n
    
    def secondary_roll_value(self, active_hero: Optional['Hero'] = None) -> int:
        """Get secondary roll value."""
        if active_hero is None:
            active_hero = self._get_active_hero()
        
        n = 0
        if self.is_familiarity:
            n = 11 if self.is_everyman else (self.familiarity_roll if self.familiarity_roll > 0 else 8)
        elif self.is_proficiency:
            n = self.proficiency_roll if self.proficiency_roll > 0 else 10
        elif self._is_focus() and active_hero is not None:
            n = active_hero.rules.skill_roll_base
            n = self._minimum_level if self._levels < 0 else (n + self._levels)
        elif active_hero is not None:
            char = active_hero.characteristic(self.characteristic)
            n3 = active_hero.rules.skill_roll_base
            n4 = active_hero.rules.skill_roll_base
            
            if char is not None and char.xmlid != "GENERAL":
                n3 = (active_hero.rules.skill_roll_base + 
                      int(round_half_up(char.get_primary_value(active_hero) / active_hero.rules.skill_roll_denominator) + 
                          float(self._levels) * self._level_value))
                n4 = (active_hero.rules.skill_roll_base + 
                      int(round_half_up(char.get_secondary_value(active_hero) / active_hero.rules.skill_roll_denominator) + 
                          float(self._levels) * self._level_value))
            else:
                if self.characteristic == 0:
                    general_level = active_hero.rules.general_level if hasattr(active_hero.rules, 'general_level') else 10
                    n3 = (active_hero.rules.skill_roll_base + 
                          int(round_half_up(float(general_level) / active_hero.rules.skill_roll_denominator) + 
                              float(self._levels) * self._level_value))
                else:
                    n3 = (active_hero.rules.skill_roll_base + 
                          int(round_half_up(float(self._levels) * self._level_value)))
                n4 = n3
            n = n4
        else:
            # Fallback when no active hero
            general_level = 10  # Default fallback
            n = 9 + int(round_half_up(float(general_level) / 5.0) + float(self._levels) * self._level_value)
        
        return n
    
    def column2_output(self, active_hero: Optional['Hero'] = None) -> str:
        """Get column 2 output."""
        if active_hero is None:
            active_hero = self._get_active_hero()
        
        if self.levels_only:
            return self.get_level_only_output()
        
        string2 = self._alias
        
        if self._name and self._name.strip():
            string2 = f"<i>{self._name}:</i> {string2}"
        
        if self.input and self.input.strip():
            string2 = f"{string2}: {self.input}"
        
        if self._selected_option is not None:
            string2 = f"{string2}: {self._selected_option.alias}"
        
        # Characteristic-based note (stub - would need HeroDesigner.getInstance().getPrefs().useWG() check)
        if (self.characteristic_choices and 
            len(self.characteristic_choices) > 1 and 
            self.characteristic != 0):
            # For now, always show characteristic if multiple choices
            string2 = f"{string2} ({characteristic_string(self.characteristic)}-based)"
        
        adder_str = self.adder_string
        if adder_str.strip():
            string2 = f"{string2} ({adder_str})"
        
        string2 = string2 + self.modifier_string
        
        if self.show_roll:
            string2 = f"{string2} {self.roll}"
        
        # END Reserve note (stub - would need END Reserve check and useWG() check)
        # if (self.get_end_usage() > 0 and ...):
        #     string2 = f"{string2} ({'uses END Reserve' if self.use_end_reserve else 'uses Personal END'})"
        
        return string2



