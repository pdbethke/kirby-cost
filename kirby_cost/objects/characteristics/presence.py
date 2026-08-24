"""
Presence characteristic class.

Converted from com.hero.objects.characteristics.Presence.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up, round_down
from kirby_cost.objects.characteristics.characteristic import _active_hero

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.objects.powers.compound_power import CompoundPower


class Presence(Characteristic, xmlid="PRE"):
    """Presence (PRE) characteristic."""
    
    def __init__(self):
        """Initialize Presence."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.PRE)
    
    def pre_attack(self, active_hero: Optional['Hero'] = None) -> str:
        """Get PRE attack damage string."""
        secondary = self.get_secondary_value(active_hero)
        primary = self.get_primary_value(active_hero)
        
        # Secondary damage
        d = (secondary - float(round_down(secondary) % 5)) / 5.0
        n = int(round_down(secondary)) % 5
        string = f"{round_half_up(d)} 1/2" if n > 2 else str(round_half_up(d))
        
        # Primary damage
        d2 = (primary - float(round_down(primary) % 5)) / 5.0
        n2 = int(round_down(primary)) % 5
        string2 = f"{round_half_up(d2)} 1/2" if n2 > 2 else str(round_half_up(d2))
        
        if string != string2:
            string = f"{string2}d6 / {string}"
        
        return f"{string}d6"
    
    @property
    def display_notes(self) -> str:
        """Get display notes with PRE attack."""
        active_hero = _active_hero()
        return f"PRE Attack: {self.pre_attack(active_hero)}"
    
    def calc_base_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate base value (overrides base class)."""
        d = 0.0
        if active_hero is not None:
            self.base_level = self.orig_base_level
            self.double_base = self.orig_base_level
            
            # Check characteristics
            for char_obj in active_hero.characteristics:
                if (char_obj.xmlid == self.xmlid or
                    char_obj.increase_levels(self.type) <= 0 or
                    char_obj.increase(self.type) == 0.0):
                    continue
                
                if isinstance(char_obj, Characteristic):
                    d3 = char_obj.pre_increase_value(active_hero)
                    self.double_base += d3
                    d += round_half_up(d3)
            
            # Check powers
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    continue
                
                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if (sub_power.xmlid == self.xmlid or
                            not isinstance(sub_power, Characteristic)):
                            continue
                        
                        char_obj = sub_power
                        if (char_obj.increase_levels(self.type) <= 0 or
                            char_obj.increase(self.type) == 0.0 or
                            not char_obj.affect_primary or
                            not CharAffectingObject.check_figured(char_obj, self.type) or
                            not char_obj.affect_total):
                            continue
                        
                        d2 = char_obj.increase_value(self.type, True)
                        self.double_base += d2
                        d += round_half_up(d2)
                elif isinstance(power, Characteristic):
                    char_obj = power
                    if (char_obj.increase_levels(self.type) <= 0 or
                        char_obj.increase(self.type) == 0.0 or
                        not char_obj.affect_primary or
                        not CharAffectingObject.check_figured(char_obj, self.type) or
                        not char_obj.affect_total):
                        continue
                    
                    d4 = char_obj.increase_value(self.type, True)
                    self.double_base += d4
                    d += round_half_up(d4)
            
            # Check equipment (similar logic)
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    continue
                
                if isinstance(equip, CompoundPower):
                    for sub_power in equip.powers:
                        if (sub_power.xmlid == self.xmlid or
                            not isinstance(sub_power, Characteristic)):
                            continue
                        
                        char_obj = sub_power
                        if (char_obj.increase_levels(self.type) <= 0 or
                            char_obj.increase(self.type) == 0.0 or
                            not char_obj.affect_primary or
                            not CharAffectingObject.check_figured(char_obj, self.type) or
                            not char_obj.affect_total):
                            continue
                        
                        d2 = char_obj.increase_value(self.type, True)
                        self.double_base += d2
                        d += round_half_up(d2)
                elif isinstance(equip, Characteristic):
                    char_obj = equip
                    if (char_obj.increase_levels(self.type) <= 0 or
                        char_obj.increase(self.type) == 0.0 or
                        not char_obj.affect_primary or
                        not CharAffectingObject.check_figured(char_obj, self.type) or
                        not char_obj.affect_total):
                        continue
                    
                    d5 = char_obj.increase_value(self.type, True)
                    self.double_base += d5
                    d += round_half_up(d5)
        
        self.base_value = min(self.base_level + d, float(self.max_val))

