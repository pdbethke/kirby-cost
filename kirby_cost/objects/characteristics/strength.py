"""
Strength characteristic class.

Converted from com.hero.objects.characteristics.Strength.java
"""

import math
from typing import Optional, TYPE_CHECKING, List

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up, round_half_down, round_down
from kirby_cost.objects.characteristics.characteristic import _active_hero

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type
    from kirby_cost.objects.powers.compound_power import CompoundPower


class Strength(Characteristic, xmlid="STR"):
    """Strength (STR) characteristic."""
    
    def __init__(self):
        """Initialize Strength."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.STR)
    
    def primary_lift(self, active_hero: Optional['Hero'] = None) -> float:
        """Calculate primary lift capacity."""
        d = 25.0
        primary = self.get_primary_value(active_hero)
        d2 = primary / 5.0
        if d2 > 0.0:
            d = math.pow(2.0, d2) * d
        else:
            d = d / math.pow(2.0, abs(d2))
        return d
    
    def secondary_lift(self, active_hero: Optional['Hero'] = None) -> float:
        """Calculate secondary lift capacity."""
        d = 25.0
        secondary = self.get_secondary_value(active_hero)
        d2 = secondary / 5.0
        if d2 > 0.0:
            d = math.pow(2.0, d2) * d
        else:
            d = d / math.pow(2.0, abs(d2))
        return d
    
    def damage_dice(self, active_hero: Optional['Hero'] = None,
                    *, primary: bool = True) -> tuple:
        """This STR's Hand-to-Hand damage as NUMBERS: (full d6, half d6).

        The same arithmetic `hth_damage_string` formats -- 5 STR to the die,
        and a remainder above 2 buying a half-die -- exposed so a consumer
        does not have to re-derive it or parse the string back.

        It exists because a consumer DID re-derive it. kirby-combat computed
        `STR // 5`, which drops the half-die: the two disagreed on 22 of 56
        STR values, and 9 of 107 corpus villains were rolled short. STR 13 is
        2 1/2d6 here and was 2d6 there.

        Reported for the primary value by default; pass primary=False for the
        secondary. NOTE this describes the NON-differentiated form, which is
        HD's default; with Increased Damage Differentiation on, a remainder
        can buy "d6-1" or a pip, which a (dice, half) pair cannot express --
        ask `hth_damage_string` for those.
        """
        value = (self.get_primary_value(active_hero) if primary
                 else self.get_secondary_value(active_hero))
        dice = (value - float(int(value) % 5)) / 5.0
        if dice < 0.0:
            dice = 0.0
        remainder = int(value) % 5
        return round_half_up(dice), remainder > 2

    def hth_damage_string(self, active_hero: Optional['Hero'] = None) -> str:
        """Get Hand-to-Hand damage string."""
        primary = self.get_primary_value(active_hero)
        secondary = self.get_secondary_value(active_hero)
        
        # Primary damage
        d = (primary - float(int(primary) % 5)) / 5.0
        if d < 0.0:
            d = 0.0
        n = int(primary) % 5
        
        use_differentiation = False
        if active_hero is not None and active_hero.rules is not None:
            use_differentiation = active_hero.rules.use_increased_damage_differentiation()
        
        if use_differentiation:
            if n == 4:
                string = f"{round_half_up(d + 1.0)}d6-1"
            elif n == 3:
                string = f"{round_half_up(d)} 1/2d6" if d > 0.0 else "1/2d6"
            elif n == 2:
                string = f"{round_half_up(d)}d6+1" if d > 0.0 else "1 pip"
            else:
                string = f"{round_half_up(d)}d6"
        else:
            if n > 2 and d > 0.0:
                string = f"{round_half_up(d)} 1/2"
            elif n > 2:
                string = "1/2"
            else:
                string = str(round_half_up(d))
            string = string + "d6"
        
        # Secondary damage
        d2 = (secondary - float(round_down(secondary) % 5)) / 5.0
        if d2 < 0.0:
            d2 = 0.0
        n2 = int(round_down(secondary)) % 5
        
        if use_differentiation:
            if n2 == 4:
                string2 = f"{round_half_up(d2 + 1.0)}d6-1"
            elif n2 == 3:
                string2 = f"{round_half_up(d2)} 1/2d6" if d2 > 0.0 else "1/2d6"
            elif n2 == 2:
                string2 = f"{round_half_up(d2)}d6+1" if d2 > 0.0 else "1 pip"
            else:
                string2 = f"{round_half_up(d2)}d6"
        else:
            if n2 > 2 and d2 > 0.0:
                string2 = f"{round_half_up(d2)} 1/2"
            elif n2 > 2:
                string2 = "1/2"
            else:
                string2 = str(round_half_up(d2))
            string2 = string2 + "d6"
        
        if string == string2:
            return string
        return f"{string}/{string2}"
    
    @property
    def display_notes(self) -> str:
        """Get display notes."""
        active_hero = _active_hero()
        hth_damage = self.hth_damage_string(active_hero)
        primary_end = self.primary_end(active_hero)
        secondary_end = self.secondary_end(active_hero)
        
        end_str = f"{primary_end}"
        if primary_end != secondary_end:
            end_str = f"{primary_end}/{secondary_end}"
        
        return f"HTH Damage {hth_damage}  END [{end_str}]"
    
    def base_end(self, active_hero: Optional['Hero'] = None) -> int:
        """Calculate base END cost."""
        if active_hero is None:
            return 0
        
        d = 0.0
        d2 = self.orig_base_level
        
        # Calculate from characteristics
        for char in active_hero.characteristics:
            if (char.xmlid == self.xmlid or
                char.increase_levels(self.type) <= 0 or
                char.increase(self.type) == 0.0):
                continue
            
            if isinstance(char, Characteristic):
                char_value = char.get_value(True, self.type, active_hero)
                increase = char.increase(self.type)
                increase_levels = char.increase_levels(self.type)
                d3 = char_value * increase / float(increase_levels)
                d += d3
        
        d2 = min(d2 + d + float(self._levels), float(self.max_val))
        d4 = d2 / self._level_value * self._level_cost
        
        # Get AP per END
        # `ap_per_end`, not `set_ap_per_end` -- the latter has never
        # existed on any class (Characteristic.ap_per_end, :623).
        n = self.ap_per_end(active_hero)
        d5 = 0.0
        d6 = 1.0
        
        # Check modifiers
        modifiers = list(self.assigned_modifiers)
        parent = self._parent
        if parent is not None:
            modifiers.extend(parent.assigned_modifiers)
        
        if GenericObject.find_object_by_id(modifiers, "CHARGES") is not None:
            n = 0
        if GenericObject.find_object_by_id(modifiers, "COSTSEND") is not None:
            if active_hero is not None and active_hero.rules is not None:
                n = active_hero.rules.get_str_ap_per_end(active_hero)
        if GenericObject.find_object_by_id(modifiers, "REDUCEDEND") is not None:
            reduced_end = GenericObject.find_object_by_id(modifiers, "REDUCEDEND")
            if reduced_end is not None and reduced_end.selected_option is not None:
                if reduced_end.selected_option.xmlid == "HALFEND":
                    n *= 2
                else:
                    n = 0
        if GenericObject.find_object_by_id(modifiers, "INCREASEDEND") is not None:
            increased_end = GenericObject.find_object_by_id(modifiers, "INCREASEDEND")
            if increased_end is not None:
                if GenericObject.find_object_by_id(increased_end.assigned_adders, "CIRCUMSTANCE") is None:
                    if increased_end.selected_option is not None:
                        d6 = increased_end.selected_option.level_value
        
        if n != 0:
            d5 = d4 / float(n)
        
        d5 *= d6
        if d5 < 0.0:
            d5 = 0.0
        
        if round_half_down(d5) == 0 and d4 > 0.0 and n != 0:
            d5 = 1.0
        
        return int(round_half_down(d5))
    
    def primary_end(self, active_hero: Optional['Hero'] = None) -> int:
        """Calculate primary END cost."""
        if active_hero is None:
            return 0
        
        d3 = float(self.base_end(active_hero))
        if d3 < 0.0:
            d3 = 0.0
        
        # Add from powers
        for power in active_hero.powers:
            if power.xmlid == self.xmlid:
                if isinstance(power, Characteristic):
                    char_obj = power
                    if char_obj.affect_primary and char_obj.affect_total:
                        d3 += float(char_obj.end_usage(active_hero))
                continue
            
            if isinstance(power, _compound_power_cls()):
                for sub_power in power.powers:
                    if sub_power.xmlid == self.xmlid:
                        if isinstance(sub_power, Characteristic):
                            char_obj = sub_power
                            if char_obj.affect_primary and char_obj.affect_total:
                                d3 += float(char_obj.end_usage)
                    elif isinstance(sub_power, CharAffectingObject):
                        char_obj = sub_power
                        if (self.orig_ap_per_end(active_hero) <= 0 or
                            char_obj.increase_levels(self.type) <= 0 or
                            not char_obj.affect_primary or
                            not CharAffectingObject.check_figured(char_obj, self.type) or
                            not char_obj.affect_total):
                            continue
                        d2 = char_obj.increase_value(self.type, True)
                        d = d2 * self._level_cost / float(self.orig_ap_per_end(active_hero))
                        d3 += d
            elif isinstance(power, CharAffectingObject):
                char_obj = power
                if (self.orig_ap_per_end(active_hero) <= 0 or
                    char_obj.increase_levels(self.type) <= 0 or
                    not char_obj.affect_primary or
                    not CharAffectingObject.check_figured(char_obj, self.type) or
                    not char_obj.affect_total):
                    continue
                d4 = char_obj.increase_value(self.type, True)
                if self.orig_ap_per_end(active_hero) > 0:
                    d2 = d4 * self._level_cost / float(self.orig_ap_per_end(active_hero))
                    d3 += d2
        
        # Add from equipment (similar logic)
        for equip in active_hero.equipment:
            if equip.xmlid == self.xmlid:
                if isinstance(equip, Characteristic):
                    char_obj = equip
                    if char_obj.affect_primary and char_obj.affect_total:
                        d3 += float(char_obj.end_usage(active_hero))
                continue
            
            if isinstance(equip, _compound_power_cls()):
                for sub_power in equip.powers:
                    if sub_power.xmlid == self.xmlid:
                        if isinstance(sub_power, Characteristic):
                            char_obj = sub_power
                            if char_obj.affect_primary and char_obj.affect_total:
                                d3 += float(char_obj.end_usage)
                    elif isinstance(sub_power, CharAffectingObject):
                        char_obj = sub_power
                        if (self.orig_ap_per_end(active_hero) <= 0 or
                            char_obj.increase_levels(self.type) <= 0 or
                            not char_obj.affect_primary or
                            not CharAffectingObject.check_figured(char_obj, self.type) or
                            not char_obj.affect_total):
                            continue
                        d2 = char_obj.increase_value(self.type, True)
                        d = d2 * self._level_cost / float(self.orig_ap_per_end(active_hero))
                        d3 += d
            elif isinstance(equip, CharAffectingObject):
                char_obj = equip
                if (self.orig_ap_per_end(active_hero) <= 0 or
                    char_obj.increase_levels(self.type) <= 0 or
                    not char_obj.affect_primary or
                    not CharAffectingObject.check_figured(char_obj, self.type) or
                    not char_obj.affect_total):
                    continue
                d5 = char_obj.increase_value(self.type, True)
                if self.orig_ap_per_end(active_hero) > 0:
                    d2 = d5 * self._level_cost / float(self.orig_ap_per_end(active_hero))
                    d3 += d2
        
        return int(round_half_down(d3))
    
    def secondary_end(self, active_hero: Optional['Hero'] = None) -> int:
        """Calculate secondary END cost."""
        if active_hero is None:
            return 0
        
        d3 = float(self.base_end(active_hero))
        if d3 < 0.0:
            d3 = 0.0
        
        # Add from powers (includes both primary and secondary affects)
        for power in active_hero.powers:
            if power.xmlid == self.xmlid:
                if isinstance(power, Characteristic):
                    char_obj = power
                    if char_obj.affect_total:
                        d3 += float(char_obj.end_usage(active_hero))
                continue
            
            if isinstance(power, _compound_power_cls()):
                for sub_power in power.powers:
                    if sub_power.xmlid == self.xmlid:
                        if isinstance(sub_power, Characteristic):
                            char_obj = sub_power
                            if char_obj.affect_primary and char_obj.affect_total:
                                d3 += float(char_obj.end_usage(active_hero))
                    elif isinstance(sub_power, CharAffectingObject):
                        char_obj = sub_power
                        if (self.orig_ap_per_end(active_hero) <= 0 or
                            char_obj.increase_levels(self.type) <= 0 or
                            not char_obj.affect_primary or
                            not CharAffectingObject.check_figured(char_obj, self.type) or
                            not char_obj.affect_total):
                            continue
                        d2 = char_obj.increase_value(self.type, True)
                        d = d2 * self._level_cost / float(self.orig_ap_per_end(active_hero))
                        d3 += d
            elif isinstance(power, CharAffectingObject):
                char_obj = power
                if (self.orig_ap_per_end(active_hero) <= 0 or
                    char_obj.increase_levels(self.type) <= 0 or
                    not CharAffectingObject.check_figured(char_obj, self.type) or
                    not char_obj.affect_total):
                    continue
                d4 = char_obj.increase_value(self.type, False)
                d4 += char_obj.increase_value(self.type, True)
                if self.orig_ap_per_end(active_hero) > 0:
                    d2 = round_half_down(d4 * self._level_cost / float(self.orig_ap_per_end(active_hero)))
                    d3 += d2
        
        # Add from equipment (similar logic)
        for equip in active_hero.equipment:
            if equip.xmlid == self.xmlid:
                if isinstance(equip, Characteristic):
                    char_obj = equip
                    if char_obj.affect_total:
                        d3 += float(char_obj.end_usage(active_hero))
                continue
            
            if isinstance(equip, _compound_power_cls()):
                for sub_power in equip.powers:
                    if sub_power.xmlid == self.xmlid:
                        if isinstance(sub_power, Characteristic):
                            char_obj = sub_power
                            if char_obj.affect_primary and char_obj.affect_total:
                                d3 += float(char_obj.end_usage(active_hero))
                    elif isinstance(sub_power, CharAffectingObject):
                        char_obj = sub_power
                        if (self.orig_ap_per_end(active_hero) <= 0 or
                            char_obj.increase_levels(self.type) <= 0 or
                            not char_obj.affect_primary or
                            not CharAffectingObject.check_figured(char_obj, self.type) or
                            not char_obj.affect_total):
                            continue
                        d2 = char_obj.increase_value(self.type, True)
                        d = d2 * self._level_cost / float(self.orig_ap_per_end(active_hero))
                        d3 += d
            elif isinstance(equip, CharAffectingObject):
                char_obj = equip
                if (self.orig_ap_per_end(active_hero) <= 0 or
                    char_obj.increase_levels(self.type) <= 0 or
                    not CharAffectingObject.check_figured(char_obj, self.type) or
                    not char_obj.affect_total):
                    continue
                d5 = char_obj.increase_value(self.type, False)
                d5 += char_obj.increase_value(self.type, True)
                if self.orig_ap_per_end(active_hero) > 0:
                    d2 = round_half_down(d5 * self._level_cost / float(self.orig_ap_per_end(active_hero)))
                    d3 += d2
        
        return int(round_half_down(d3))
    
    def value(self, figured: bool, char_type: int, active_hero: Optional['Hero'] = None) -> float:
        """Get value (figured or base)."""
        if figured:
            return self.figured_base_value(char_type, active_hero)
        return self.get_base_value(active_hero)
    
    def figured_base_value(self, char_type: int, active_hero: Optional['Hero'] = None) -> float:
        """Get figured base value (stub - needs full implementation)."""
        return self.get_base_value(active_hero)
    
    @property
    def use_end_reserve(self) -> bool:
        """Check if this uses END Reserve."""
        # hasattr(self, 'use_end_reserve') asked about THIS PROPERTY, which
        # re-entered it -- infinite recursion. The backing field is what the
        # guard meant. Never fired before 2026-08-24 because nothing
        # instantiated Strength.
        return self._use_end_reserve if hasattr(self, '_use_end_reserve') else False
    


def _compound_power_cls():
    """CompoundPower, imported at call time.

    A module-level import would be circular. The class was only ever imported
    under TYPE_CHECKING, so every `isinstance(power, _compound_power_cls())` below
    raised NameError at runtime -- unnoticed, because nothing instantiated
    Strength until 2026-08-24.
    """
    from kirby_cost.objects.powers.compound_power import CompoundPower
    return CompoundPower
