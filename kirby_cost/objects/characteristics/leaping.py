"""
Leaping characteristic class.

Converted from com.hero.objects.characteristics.Leaping.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up, round_down

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.objects.powers.compound_power import CompoundPower
    from kirby_cost.objects.powers.power import Power


class Leaping(Characteristic, xmlid="LEAPING"):
    """Leaping movement characteristic."""
    
    def __init__(self):
        """Initialize Leaping."""
        super().__init__(self.XMLID)
        # Forward/upward movement values
        self.primary_forward: float = 0.0
        self.primary_upward: float = 0.0
        self.secondary_forward: float = 0.0
        self.secondary_upward: float = 0.0
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.LEAPING)
    
    def calc_base_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate base value (overrides base class)."""
        d = 0.0
        self.double_base = 0.0
        
        if active_hero is not None:
            # Check characteristics
            for char_obj in active_hero.characteristics:
                if (char_obj.xmlid == self.xmlid or
                    char_obj.increase_levels(self.type) <= 0 or
                    char_obj.increase(self.type) == 0.0):
                    continue
                
                if isinstance(char_obj, Characteristic):
                    char_value = char_obj.characteristic_value(active_hero)
                    increase = char_obj.increase(self.type)
                    increase_levels = char_obj.increase_levels(self.type)
                    d3 = char_value * increase / float(increase_levels)
                    self.double_base += d3
                    d += round_down(d3 * 2.0) / 2.0
            
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
                        d += round_down(d2 * 2.0) / 2.0
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
                    d += round_down(d4 * 2.0) / 2.0
            
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
                        d += round_down(d2 * 2.0) / 2.0
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
                    d += round_down(d5 * 2.0) / 2.0
        
        d = round_down(self.double_base * 2.0) / 2.0
        if self.base_level + d < float(self._minimum_level):
            self.base_value = float(self._minimum_level)
        elif self.base_level + d < float(self.max_val):
            self.base_value = self.base_level + d
        else:
            self.base_value = float(self.max_val) - d
        
    def get_primary_forward(self, active_hero: Optional['Hero'] = None) -> float:
        """Get primary forward movement."""
        self._calc_primary_forward(active_hero)
        return self.primary_forward
    
    def _calc_primary_forward(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate primary forward movement."""
        d = 0.0
        if active_hero is not None:
            self.double_base = self.characteristic_value(active_hero)
            
            # Check powers (excluding upward-only)
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    if GenericObject.find_object_by_id(power.assigned_modifiers, "UPWARDMOVEMENTONLY") is None:
                        if isinstance(power, Characteristic):
                            char_obj = power
                            if char_obj.affect_primary and char_obj.affect_total:
                                d += float(char_obj.levels)
                                self.double_base += float(char_obj.levels)
                    continue
                
                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if sub_power.xmlid == self.xmlid:
                            if GenericObject.find_object_by_id(sub_power.assigned_modifiers, "UPWARDMOVEMENTONLY") is None:
                                if isinstance(sub_power, Characteristic):
                                    char_obj = sub_power
                                    if char_obj.affect_primary and char_obj.affect_total:
                                        d += float(char_obj.levels)
                                        self.double_base += float(char_obj.levels)
                        elif isinstance(sub_power, CharAffectingObject):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                not char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d2 = char_obj.increase_value(self.type, True)
                            self.double_base += d2
                            d += d2
                elif isinstance(power, CharAffectingObject):
                    char_obj = power
                    if (char_obj.increase_levels(self.type) <= 0 or
                        char_obj.increase(self.type) == 0.0 or
                        not char_obj.affect_primary or
                        not CharAffectingObject.check_figured(char_obj, self.type) or
                        not char_obj.affect_total):
                        continue
                    d3 = char_obj.increase_value(self.type, True)
                    self.double_base += d3
                    d += d3
            
            # Check equipment (similar logic)
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    if GenericObject.find_object_by_id(equip.assigned_modifiers, "UPWARDMOVEMENTONLY") is None:
                        if isinstance(equip, Characteristic):
                            char_obj = equip
                            if char_obj.affect_primary and char_obj.affect_total:
                                d += float(char_obj.levels)
                                self.double_base += float(char_obj.levels)
                    continue
                
                if isinstance(equip, CompoundPower):
                    for sub_power in equip.powers:
                        if sub_power.xmlid == self.xmlid:
                            if GenericObject.find_object_by_id(sub_power.assigned_modifiers, "UPWARDMOVEMENTONLY") is None:
                                if isinstance(sub_power, Characteristic):
                                    char_obj = sub_power
                                    if char_obj.affect_primary and char_obj.affect_total:
                                        d += float(char_obj.levels)
                                        self.double_base += float(char_obj.levels)
                        elif isinstance(sub_power, CharAffectingObject):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                not char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d2 = char_obj.increase_value(self.type, True)
                            self.double_base += d2
                            d += d2
                elif isinstance(equip, CharAffectingObject):
                    char_obj = equip
                    if (char_obj.increase_levels(self.type) <= 0 or
                        char_obj.increase(self.type) == 0.0 or
                        not char_obj.affect_primary or
                        not CharAffectingObject.check_figured(char_obj, self.type) or
                        not char_obj.affect_total):
                        continue
                    d4 = char_obj.increase_value(self.type, True)
                    self.double_base += d4
                    d += d4
        
        self.primary_forward = min(self.double_base, float(self.max_val))

    def get_primary_upward(self, active_hero: Optional['Hero'] = None) -> float:
        """Get primary upward movement."""
        self._calc_primary_upward(active_hero)
        return self.primary_upward
    
    def _calc_primary_upward(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate primary upward movement."""
        d = 0.0
        bl = True  # Gravity penalty flag
        
        if active_hero is not None:
            self.double_base = self.characteristic_value(active_hero)
            
            # Check powers (excluding forward-only)
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    if GenericObject.find_object_by_id(power.assigned_modifiers, "FORWARDMOVEMENTONLY") is None:
                        if isinstance(power, Characteristic):
                            char_obj = power
                            if char_obj.affect_primary and char_obj.affect_total:
                                d += float(char_obj.levels) / 2.0
                                # Check for NOGRAVITYPENALTY modifier
                                if GenericObject.find_object_by_id(char_obj.assigned_modifiers, "NOGRAVITYPENALTY") is not None:
                                    if char_obj.add_modifiers_to_base:
                                        bl = False
                                    d += float(char_obj.levels) / 2.0
                    continue
                
                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if sub_power.xmlid == self.xmlid:
                            if GenericObject.find_object_by_id(sub_power.assigned_modifiers, "FORWARDMOVEMENTONLY") is None:
                                if isinstance(sub_power, Characteristic):
                                    char_obj = sub_power
                                    if char_obj.affect_primary and char_obj.affect_total:
                                        d += float(char_obj.levels) / 2.0
                                        if GenericObject.find_object_by_id(char_obj.assigned_modifiers, "NOGRAVITYPENALTY") is not None:
                                            if char_obj.add_modifiers_to_base:
                                                bl = False
                                            d += float(char_obj.levels) / 2.0
                        elif isinstance(sub_power, Power):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                not char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d2 = char_obj.increase_value(self.type, True)
                            d += d2 / 2.0
                elif isinstance(power, Power):
                    char_obj = power
                    if (char_obj.increase_levels(self.type) <= 0 or
                        char_obj.increase(self.type) == 0.0 or
                        not char_obj.affect_primary or
                        not CharAffectingObject.check_figured(char_obj, self.type) or
                        not char_obj.affect_total):
                        continue
                    d3 = char_obj.increase_value(self.type, True)
                    d += d3 / 2.0
            
            # Check equipment (similar logic)
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    if GenericObject.find_object_by_id(equip.assigned_modifiers, "FORWARDMOVEMENTONLY") is None:
                        if isinstance(equip, Characteristic):
                            char_obj = equip
                            if char_obj.affect_primary and char_obj.affect_total:
                                d += float(char_obj.levels) / 2.0
                                if GenericObject.find_object_by_id(char_obj.assigned_modifiers, "NOGRAVITYPENALTY") is not None:
                                    if char_obj.add_modifiers_to_base:
                                        bl = False
                                    d += float(char_obj.levels) / 2.0
                    continue
                
                if isinstance(equip, CompoundPower):
                    for sub_power in equip.powers:
                        if sub_power.xmlid == self.xmlid:
                            if GenericObject.find_object_by_id(sub_power.assigned_modifiers, "FORWARDMOVEMENTONLY") is None:
                                if isinstance(sub_power, Characteristic):
                                    char_obj = sub_power
                                    if char_obj.affect_primary and char_obj.affect_total:
                                        d += float(char_obj.levels) / 2.0
                                        if GenericObject.find_object_by_id(char_obj.assigned_modifiers, "NOGRAVITYPENALTY") is not None:
                                            if char_obj.add_modifiers_to_base:
                                                bl = False
                                            d += float(char_obj.levels) / 2.0
                        elif isinstance(sub_power, Power):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                not char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d2 = char_obj.increase_value(self.type, True)
                            d += d2 / 2.0
                elif isinstance(equip, Power):
                    char_obj = equip
                    if (char_obj.increase_levels(self.type) <= 0 or
                        char_obj.increase(self.type) == 0.0 or
                        not char_obj.affect_primary or
                        not CharAffectingObject.check_figured(char_obj, self.type) or
                        not char_obj.affect_total):
                        continue
                    d4 = char_obj.increase_value(self.type, True)
                    d += d4 / 2.0
        
        # Apply gravity penalty: half if bl is True, full if False
        self.primary_upward = (self.double_base / 2.0 + d) if bl else (self.double_base + d)
        if self.primary_upward > float(self.max_val):
            self.primary_upward = float(self.max_val)
    def get_secondary_forward(self, active_hero: Optional['Hero'] = None) -> float:
        """Get secondary forward movement."""
        self._calc_secondary_forward(active_hero)
        return self.secondary_forward
    
    def _calc_secondary_forward(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate secondary forward movement."""
        d2 = 0.0
        if active_hero is not None:
            # Check powers (excluding upward-only, secondary affects)
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    if GenericObject.find_object_by_id(power.assigned_modifiers, "UPWARDMOVEMENTONLY") is None:
                        if isinstance(power, Characteristic):
                            char_obj = power
                            if not char_obj.affect_primary and char_obj.affect_total:
                                d2 += float(char_obj.levels)
                    continue
                
                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if sub_power.xmlid == self.xmlid:
                            if GenericObject.find_object_by_id(sub_power.assigned_modifiers, "UPWARDMOVEMENTONLY") is None:
                                if isinstance(sub_power, Characteristic):
                                    char_obj = sub_power
                                    if not char_obj.affect_primary and char_obj.affect_total:
                                        d2 += float(char_obj.levels)
                        elif isinstance(sub_power, CharAffectingObject):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d = char_obj.increase_value(self.type, False)
                            d2 += d
                elif isinstance(power, CharAffectingObject):
                    char_obj = power
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d3 = char_obj.increase_value(self.type, False)
                    d2 += d3
            
            # Check equipment (similar logic)
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    if GenericObject.find_object_by_id(equip.assigned_modifiers, "UPWARDMOVEMENTONLY") is None:
                        if isinstance(equip, Characteristic):
                            char_obj = equip
                            if not char_obj.affect_primary and char_obj.affect_total:
                                d2 += float(char_obj.levels)
                    continue
                
                if isinstance(equip, CompoundPower):
                    for sub_power in equip.powers:
                        if sub_power.xmlid == self.xmlid:
                            if GenericObject.find_object_by_id(sub_power.assigned_modifiers, "UPWARDMOVEMENTONLY") is None:
                                if isinstance(sub_power, Characteristic):
                                    char_obj = sub_power
                                    if not char_obj.affect_primary and char_obj.affect_total:
                                        d2 += float(char_obj.levels)
                        elif isinstance(sub_power, CharAffectingObject):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d = char_obj.increase_value(self.type, False)
                            d2 += d
                elif isinstance(equip, CharAffectingObject):
                    char_obj = equip
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d4 = char_obj.increase_value(self.type, False)
                    d2 += d4
        
        self.secondary_forward = min(self.get_primary_forward(active_hero) + d2, float(self.max_val))

    def get_secondary_upward(self, active_hero: Optional['Hero'] = None) -> float:
        """Get secondary upward movement."""
        self._calc_secondary_upward(active_hero)
        return self.secondary_upward
    
    def _calc_secondary_upward(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate secondary upward movement."""
        d2 = 0.0
        if active_hero is not None:
            # Check powers (excluding forward-only, secondary affects)
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    if GenericObject.find_object_by_id(power.assigned_modifiers, "FORWARDMOVEMENTONLY") is None:
                        if isinstance(power, Characteristic):
                            char_obj = power
                            if not char_obj.affect_primary and char_obj.affect_total:
                                d2 += float(char_obj.levels) / 2.0
                                if GenericObject.find_object_by_id(char_obj.assigned_modifiers, "NOGRAVITYPENALTY") is not None:
                                    d2 += float(char_obj.levels) / 2.0
                    continue
                
                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if sub_power.xmlid == self.xmlid:
                            if GenericObject.find_object_by_id(sub_power.assigned_modifiers, "FORWARDMOVEMENTONLY") is None:
                                if isinstance(sub_power, Characteristic):
                                    char_obj = sub_power
                                    if not char_obj.affect_primary and char_obj.affect_total:
                                        d2 += float(char_obj.levels) / 2.0
                                        if GenericObject.find_object_by_id(char_obj.assigned_modifiers, "NOGRAVITYPENALTY") is not None:
                                            d2 += float(char_obj.levels) / 2.0
                        elif isinstance(sub_power, Power):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d = char_obj.increase_value(self.type, False)
                            self.double_base += d
                            d2 += d / 2.0
                elif isinstance(power, Power):
                    char_obj = power
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d3 = char_obj.increase_value(self.type, False)
                    d2 += d3 / 2.0
            
            # Check equipment (similar logic)
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    if GenericObject.find_object_by_id(equip.assigned_modifiers, "FORWARDMOVEMENTONLY") is None:
                        if isinstance(equip, Characteristic):
                            char_obj = equip
                            if not char_obj.affect_primary and char_obj.affect_total:
                                d2 += float(char_obj.levels) / 2.0
                                if GenericObject.find_object_by_id(char_obj.assigned_modifiers, "NOGRAVITYPENALTY") is not None:
                                    d2 += float(char_obj.levels) / 2.0
                    continue
                
                if isinstance(equip, CompoundPower):
                    for sub_power in equip.powers:
                        if sub_power.xmlid == self.xmlid:
                            if GenericObject.find_object_by_id(sub_power.assigned_modifiers, "FORWARDMOVEMENTONLY") is None:
                                if isinstance(sub_power, Characteristic):
                                    char_obj = sub_power
                                    if not char_obj.affect_primary and char_obj.affect_total:
                                        d2 += float(char_obj.levels) / 2.0
                                        if GenericObject.find_object_by_id(char_obj.assigned_modifiers, "NOGRAVITYPENALTY") is not None:
                                            d2 += float(char_obj.levels) / 2.0
                        elif isinstance(sub_power, Power):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d = char_obj.increase_value(self.type, False)
                            self.double_base += d
                            d2 += d / 2.0
                elif isinstance(equip, Power):
                    char_obj = equip
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d4 = char_obj.increase_value(self.type, False)
                    d2 += d4 / 2.0
        
        self.secondary_upward = min(self.get_primary_upward(active_hero) + d2, float(self.max_val))

