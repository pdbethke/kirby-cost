"""
Ego characteristic class.

Converted from com.hero.objects.characteristics.Ego.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.objects.powers.power import Power


class Ego(Characteristic, xmlid="EGO"):
    """Ego (EGO) characteristic."""
    
    def __init__(self):
        """Initialize Ego."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.EGO)
    
    def display_notes(self, active_hero: Optional['Hero'] = None) -> str:
        """Get display notes with ECV calculations."""
        # In 6E, EGO doesn't show ECV in display notes
        # This would need to check template version
        if active_hero is None:
            return ""
        
        # Check if 6E (stub - would need template access)
        # if active_hero.template.is_6e():
        #     return ""
        
        d = 0.0  # Primary ECV
        d2 = 0.0  # Secondary ECV
        
        if active_hero is not None:
            self.base_level = self.orig_base_level
            self.double_base = self.orig_base_level
            
            # Calculate from characteristics
            for char_obj in active_hero.characteristics:
                if isinstance(char_obj, Characteristic):
                    if char_obj.ecv_increase_levels <= 0 or char_obj.ecv_increase == 0.0:
                        continue
                    
                    d3 = char_obj.primary_value(active_hero) * char_obj.ecv_increase / float(char_obj.ecv_increase_levels)
                    d += d3
                    d3 = char_obj.secondary_value(active_hero) * char_obj.ecv_increase / float(char_obj.ecv_increase_levels)
                    d2 += d3
            
            # Calculate from powers
            for power in active_hero.powers:
                if not isinstance(power, Power):
                    continue
                
                char_obj = power
                if (char_obj.ecv_increase_levels <= 0 or
                    not CharAffectingObject.check_figured(char_obj, self.type) or
                    char_obj.ecv_increase <= 0.0):
                    continue
                
                d3 = float(char_obj.levels) * char_obj.ecv_increase / float(char_obj.ecv_increase_levels)
                if char_obj.affect_primary:
                    d += d3
                d2 += d3
            
            # Calculate from equipment
            for equip in active_hero.equipment:
                if not isinstance(equip, Power):
                    continue
                
                char_obj = equip
                if (char_obj.ecv_increase_levels <= 0 or
                    not CharAffectingObject.check_figured(char_obj, self.type) or
                    char_obj.ecv_increase <= 0.0):
                    continue
                
                d3 = float(char_obj.levels) * char_obj.ecv_increase / float(char_obj.ecv_increase_levels)
                if char_obj.affect_primary:
                    d += d3
                d2 += d3
        
        string = f"ECV: {round_half_up(d)}"
        if d != d2:
            string = f"{string}/{round_half_up(d2)}"
        
        return string

