"""
TransportFamiliarity skill class for kirby-cost.

Converted from com.hero.objects.skills.TransportFamiliarity.java
"""

from typing import Optional, TYPE_CHECKING, List
from kirby_cost.objects.skills.adder_based_skill import AdderBasedSkill
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import characteristic_string

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.objects.adder import Adder


class TransportFamiliarity(AdderBasedSkill, xmlid="TRANSPORT_FAMILIARITY"):
    """Transport Familiarity skill."""
    
    _roll_based_default = False
    
    def __init__(self, xmlid: str = None):
        """Initialize TransportFamiliarity."""
        super().__init__(xmlid or self.XMLID)
        self._alias = "TF"
        self.combat_driving_discounted: bool = False
        self.combat_piloting_discounted: bool = False
        self.riding_discounted: bool = False
    
    def _check_for_bonus(self, skill_type: str, adders: List['Adder']) -> bool:
        """Check for bonus adder of given type."""
        for adder in adders:
            if adder.contains_type(skill_type) and adder.total_cost == 1.0:
                return True
            if (adder.assigned_adders and 
                len(adder.assigned_adders) > 0 and 
                not adder.is_selected):
                if self._check_for_bonus(skill_type, adder.assigned_adders):
                    return True
        return False
    
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
    def column3_output(self) -> str:
        """Get column 3 output (empty for transport familiarity)."""
        return ""
    
    @property
    def roll(self) -> str:
        """Get roll (empty for transport familiarity)."""
        return ""
    
    def _get_loaded_hero(self):
        """Get the loaded hero for discount lookups."""
        if hasattr(self, '_loaded_hero') and self._loaded_hero is not None:
            return self._loaded_hero
        return self._get_active_hero()

    @property
    def total_cost(self) -> float:
        """Get total cost with discount logic."""
        active_hero = self._get_loaded_hero()
        d = super().total_cost
        
        combat_driving = False
        combat_piloting = False
        riding = False
        
        adders = self.assigned_adders
        combat_driving = self._check_for_bonus("DRIVING", adders)
        combat_piloting = self._check_for_bonus("PILOTING", adders)
        riding = self._check_for_bonus("RIDING", adders)
        
        if combat_driving and active_hero is not None:
            combat_driving = False
            skills = active_hero.skills
            for skill in skills:
                if skill.xmlid.upper() == "COMBAT_DRIVING":
                    combat_driving = True
                    break
        
        if combat_piloting and active_hero is not None:
            combat_piloting = False
            skills = active_hero.skills
            for skill in skills:
                if skill.xmlid.upper() == "COMBAT_PILOTING":
                    combat_piloting = True
                    break
        
        if riding and active_hero is not None:
            riding = False
            skills = active_hero.skills
            for skill in skills:
                if skill.xmlid.upper() == "RIDING":
                    riding = True
                    break
        
        if (combat_driving or combat_piloting or riding) and active_hero is not None:
            skills = active_hero.skills
            for skill in skills:
                if (skill.xmlid == self.xmlid and 
                    skill._id != self._id):
                    tf_skill = skill
                    if isinstance(tf_skill, TransportFamiliarity):
                        if tf_skill._is_combat_driving_discounted():
                            combat_driving = False
                        if tf_skill._is_combat_piloting_discounted():
                            combat_piloting = False
                        if tf_skill._is_riding_discounted():
                            riding = False
        
        if combat_driving:
            self.combat_driving_discounted = True
            d += -1.0
        if combat_piloting:
            self.combat_piloting_discounted = True
            d += -1.0
        if riding:
            self.riding_discounted = True
            d += -1.0
        
        return d
    
    
    def _is_combat_driving_discounted(self) -> bool:
        """Check if combat driving is discounted."""
        return self.combat_driving_discounted
    
    def _is_combat_piloting_discounted(self) -> bool:
        """Check if combat piloting is discounted."""
        return self.combat_piloting_discounted
    
    def _is_riding_discounted(self) -> bool:
        """Check if riding is discounted."""
        return self.riding_discounted

    def _is_transport_familiarity(self) -> bool:
        """This IS a Transport Familiarity."""
        return True



