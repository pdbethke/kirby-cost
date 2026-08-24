"""
Speed characteristic class.

Converted from com.hero.objects.characteristics.Speed.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up, round_half_down, round_down
from kirby_cost.objects.characteristics.characteristic import _active_hero

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.objects.powers.compound_power import CompoundPower
    from kirby_cost.objects.powers.automaton import Automaton


class Speed(Characteristic, xmlid="SPD"):
    """Speed (SPD) characteristic."""
    
    def __init__(self):
        """Initialize Speed."""
        super().__init__(self.XMLID)
        self.double_base = self.base_level
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.SPD)
    
    def calc_base_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate base value (overrides base class)."""
        d = 0.0
        
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
                    d += d3
            
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
                        d += d2
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
                    d += d4
            
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
                        d += d2
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
                    d += d5
        
        self.base_value = min(round_down(self.base_level + d), float(self.max_val)) if round_down(self.base_level + d) <= self.max_val else float(self.max_val)
    
    def _calc_ncm_char_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate NCM characteristic value (overrides base class)."""
        d = float(self._levels) + self.orig_base_level
        
        if active_hero is not None:
            for char in active_hero.characteristics:
                if (char.xmlid == self.xmlid or
                    char.increase_levels(self.type) <= 0 or
                    char.increase(self.type) == 0.0):
                    continue
                
                if isinstance(char, Characteristic):
                    ncm_value = char.ncm_char_value(active_hero)
                    increase = char.increase(self.type)
                    increase_levels = char.increase_levels(self.type)
                    d2 = ncm_value * increase / float(increase_levels)
                    self.double_base += d2
                    d += d2
        
        self.ncm_char_value = min(d, float(self.max_val))
    
    def _calc_secondary_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate secondary value (overrides base class)."""
        d2 = 0.0
        
        if active_hero is not None:
            # Check powers
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    char_obj = power
                    if char_obj.affect_primary or not char_obj.affect_total:
                        continue
                    d2 += float(char_obj.levels)
                    continue
                
                if isinstance(power, CharAffectingObject):
                    char_obj = power
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d = char_obj.increase_value(self.type, False)
                    d2 += round_down(d)
            
            # Check equipment
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    char_obj = equip
                    if char_obj.affect_primary or not char_obj.affect_total:
                        continue
                    d2 += float(char_obj.levels)
                    continue
                
                if isinstance(equip, CharAffectingObject):
                    char_obj = equip
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d = char_obj.increase_value(self.type, False)
                    d2 += round_down(d)
        
        d3 = self.get_primary_value(active_hero) + d2
        self.secondary_value = min(round_down(d3), float(self.max_val))
    
    def characteristic_base(self, active_hero: Optional['Hero'] = None) -> str:
        """Get characteristic base as string (overrides base class)."""
        from decimal import Decimal, ROUND_HALF_UP
        big_decimal = Decimal(str(self.get_base_value(active_hero)))
        big_decimal = big_decimal.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        return str(big_decimal)
    
    def characteristic_value(self, active_hero: Optional['Hero'] = None) -> float:
        """Get characteristic value (overrides base class)."""
        return round_down(self.get_base_value(active_hero) + float(self._levels))
    
    @property
    def display_notes(self) -> str:
        """Get display notes with phase information."""
        active_hero = _active_hero()
        string = ""
        string2 = ""
        
        d = self.get_primary_value(active_hero)
        if d > 12.0:
            d = 12.0
        
        # Phase mapping based on SPD value
        phase_map = {
            0: "(none)",
            1: "7",
            2: "6, 12",
            3: "4, 8, 12",
            4: "3, 6, 9, 12",
            5: "3, 5, 8, 10, 12",
            6: "2, 4, 6, 8, 10, 12",
            7: "2, 4, 6, 7, 9, 11, 12",
            8: "2, 3, 5, 6, 8, 9, 11, 12",
            9: "2, 3, 4, 6, 7, 8, 10, 11, 12",
            10: "2, 3, 4, 5, 6, 8, 9, 10, 11, 12",
            11: "2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12",
            12: "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12",
        }
        
        string = phase_map.get(int(round_down(d)), "???")
        
        d = self.get_secondary_value(active_hero)
        if d > 12.0:
            d = 12.0
        
        string2 = phase_map.get(int(round_down(d)), "???")
        
        if string != string2:
            string = f"{string}/{string2}"
        
        return f"Phases:  {string}"
    
    def roll(self, active_hero: Optional['Hero'] = None) -> str:
        """Speed doesn't have a roll."""
        return ""
    
    @property
    def total_cost(self) -> float:
        """Get total cost (overrides base class)."""
        active_hero = None  # Parameter removed — never passed
        d5 = self.base_cost
        
        if not self._is_power:
            d4 = self.get_value(False, self.type, active_hero)
            d3 = self.get_base_value(active_hero)
            if d4 < d3:
                d3 = round_down(d3)
            
            d2 = d4 - d3
            if abs(d2) < 1.0 and d2 < 0.0:
                d2 = 0.0
            
            d = d2 / self._level_value * self._level_cost
            d5 += round_half_down(d)
        else:
            d5 += float(self._levels) * self._level_cost / self._level_value
        
        # NCM handling (stub - would need template/rules access)
        # if (template.is_6e() or (active_hero.is_ncm_selected() and template.get_ncm_cost_multiplier() > 0 and
        #     not self.is_power() and (self.levels > 0 or self.get_true_base() > self.get_ncm_level()) and
        #     self.get_ncm_char_value(active_hero) > self.get_ncm_level() and not self.is_power())):
        #     ...
        
        # Add assigned adders (positive cost)
        for adder in self.assigned_adders:
            real_cost = adder.total_cost
            if real_cost > 0.0:
                d5 += real_cost
        
        # Apply min/max cost limits
        if d5 < self._minimum_cost and self.min_set:
            d5 = self._minimum_cost
        elif d5 > self._max_cost and self.max_set:
            d5 = self._max_cost
        
        # Add assigned adders (negative cost)
        for adder in self.assigned_adders:
            real_cost = adder.total_cost
            if real_cost < 0.0:
                d5 += real_cost
        
        # Automaton defense cost multiplier (stub - would need Automaton power)
        if (self.types and "DEFENSE" in self.types and
            active_hero is not None):
            automaton = GenericObject.find_object_by_id(active_hero.powers, "AUTOMATON")
            if automaton is not None:
                if automaton.selected_option is not None:
                    option_xmlid = automaton.selected_option.xmlid.upper()
                    if option_xmlid.startswith("NOSTUN"):
                        d5 *= float(automaton.defense_cost_multiplier)
        
        return d5
    
    def get_value(self, figured: bool, char_type: int, active_hero: Optional['Hero'] = None) -> float:
        """Get value (figured or base) - overrides base class."""
        d = self.figured_base_value(char_type, active_hero) if figured else self.get_base_value(active_hero)
        d = round_down(d)
        
        if d + float(self._levels) < float(self._minimum_level):
            self._levels = int(float(self._minimum_level - self.get_base_value(active_hero)))
            return float(self._minimum_level)
        
        if d + float(self._levels) <= float(self.max_val):
            return d + float(self._levels)
        
        self._levels = int(float(self.max_val - self.get_base_value(active_hero)))
        return float(self.max_val)
    
    def value_display(self, active_hero: Optional['Hero'] = None) -> str:
        """Get value display (overrides base class)."""
        primary = self.get_primary_value(active_hero)
        secondary = self.get_secondary_value(active_hero)
        
        if primary != secondary:
            return f"{round_down(primary)}/{round_down(secondary)}"
        return str(round_half_up(primary))
    
    def set_value(self, value: float, active_hero: Optional['Hero'] = None) -> None:
        """Set value (overrides base class)."""
        from kirby_cost.util.rounder import round_up
        
        d2 = self.characteristic_value(active_hero)
        if value == d2:
            return
        
        if value < float(self._minimum_level):
            self._levels = int(round_up(float(self._minimum_level - value)))
        
        if value <= float(self.max_val):
            self._levels = int(round_up(value - self.get_base_value(active_hero)))
        else:
            self._levels = int(round_up(float(self.max_val - self.get_base_value(active_hero))))

