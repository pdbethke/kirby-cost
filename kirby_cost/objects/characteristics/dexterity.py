"""
Dexterity characteristic class.

Converted from com.hero.objects.characteristics.Dexterity.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up
from kirby_cost.objects.characteristics.characteristic import _active_hero

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type


class Dexterity(Characteristic, xmlid="DEX"):
    """Dexterity (DEX) characteristic."""
    
    def __init__(self):
        """Initialize Dexterity."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.DEX)
    
    @property
    def display_notes(self) -> str:
        """Get display notes with OCV/DCV calculations."""
        active_hero = _active_hero()
        # In 6E, DEX doesn't show OCV/DCV in display notes
        # This would need to check template version
        # For now, return empty for 6E
        if active_hero is None:
            return ""
        
        # Check if 6E (stub - would need template access)
        # if active_hero.template.is_6e():
        #     return ""
        
        d = 0.0  # Primary OCV
        d2 = 0.0  # Primary DCV
        
        # Calculate primary OCV/DCV
        for char in active_hero.characteristics:
            if isinstance(char, Characteristic):
                if char.ocv_increase_levels != 0:
                    n = -1 if char.ocv_increase < 0.0 else 1
                    d3 = abs(char.ocv_increase) * char.primary_value(active_hero) / float(char.ocv_increase_levels)
                    d += d3 * float(n)
                
                if char.dcv_increase_levels != 0:
                    d2 += float(char.dcv_effect(True, active_hero))
        
        # Calculate secondary OCV/DCV
        d4 = 0.0  # Secondary OCV
        d5 = 0.0  # Secondary DCV
        
        for char in active_hero.characteristics:
            if isinstance(char, Characteristic):
                if char.ocv_increase_levels != 0:
                    n = -1 if char.ocv_increase < 0.0 else 1
                    d6 = abs(char.ocv_increase) * char.secondary_value(active_hero) / float(char.ocv_increase_levels)
                    d4 += d6 * float(n)
                
                if char.dcv_increase_levels != 0:
                    d5 += float(char.dcv_effect(False, active_hero))
        
        string = f"OCV {round_half_up(d)}"
        if d != d4:
            string = f"{string}/{round_half_up(d4)}"
        
        string = f"{string} DCV {round_half_up(d2)}"
        if d2 != d5:
            string = f"{string}/{round_half_up(d5)}"
        
        return string

