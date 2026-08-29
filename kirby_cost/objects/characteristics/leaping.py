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
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type
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
        
    #: 6E throughout: the corpus and the template chain are 6E, so distances
    #: are metres. HD carries an inches form for earlier editions.
    UNIT = "m"

    def _distance(self, value: float, *, upward: bool) -> str:
        """One distance, with HD's half-metre rules.

        Ported from ``Leaping.getDisplayNotes`` (Leaping.java:801). Forward and
        upward are NOT formatted the same way, and the difference matters: a
        forward distance shows "N 1/2" only when the whole part is over 1,
        while an upward distance below a metre prints a bare "1/2m" with no
        leading number. Forward has no equivalent branch.

        The ``getLevels() >= 0`` half of each condition is HD's: a character
        who has SOLD leaping down does not get a fractional readout.
        """
        whole = round_down(value)
        has_half = (value - whole) >= 0.5
        if has_half and (value > 1 or self.levels >= 0):
            return f"{whole} 1/2{self.UNIT}"
        if upward and has_half and (value > 0 or self.levels >= 0):
            return f"1/2{self.UNIT}"
        return f"{whole}{self.UNIT}"

    @property
    def display_notes(self) -> str:
        """``4m forward, 2m upward`` — the parenthetical HD prints for a leap.

        A leap has two distances, and the rules relate them: "All characters
        have a base forward leap of 4m and a base upward leap of 2m (half the
        forward leap)" (6E Volume 2, p30). Primary and secondary are shown
        slashed when they disagree, which happens when a power boosts only one
        of them.
        """
        hero = _active_hero()
        pf = self.get_primary_forward(hero)
        pu = self.get_primary_upward(hero)
        sf = self.get_secondary_forward(hero)
        su = self.get_secondary_upward(hero)

        p_for = self._distance(pf, upward=False)
        p_up = self._distance(pu, upward=True)
        if pf != sf or pu != su:
            s_for = self._distance(sf, upward=False)
            s_up = self._distance(su, upward=True)
            return f"{p_for}/{s_for} forward, {p_up}/{s_up} upward"
        return f"{p_for} forward, {p_up} upward"

    @property
    def damage_display(self) -> str:
        """The levels bought, with a unit and a sign only when adding."""
        prefix = "+" if (self.affect_total and self.levels > 0) else ""
        return f"{prefix}{self.levels}{self.UNIT}"

    @property
    def column2_output(self) -> str:
        """``Leaping -2m (4m forward, 2m upward)``.

        Ported from ``Leaping.getColumn2Output`` (Leaping.java:737). Unlike
        Running, the parenthetical is the two leap distances rather than a
        single total, and unlike the base Characteristic the alias leads.
        """
        alias = self._alias or self._display or self.xmlid
        name = (self._name or "").strip()
        modifier_str = self.modifier_string or ""

        if self.levels == 0 and self.add_modifiers_to_base and modifier_str.strip():
            string = modifier_str.strip()
            if string.startswith(","):
                string = string[1:].strip()
            string = f"{string} applied to {alias}"
            if name:
                string = f"<i>{name}:</i>  {string}"
            return string

        string = alias
        if name:
            string = f"<i>{name}:</i>  {string}"
        string = f"{string} {self.damage_display}"
        if self.affect_total:
            string = f"{string} ({self.display_notes})"
        if self.input and self.input.strip():
            string = f"{string}:  {self.input}"

        adder_str = (self.adder_string or "").strip()
        if self._selected_option:
            option = self._selected_option
            option_alias = option.alias or option.display or option.xmlid
            string = f"{string} ({option_alias}"
            if adder_str:
                string = f"{string}; {adder_str}"
            string = f"{string})"
        elif adder_str:
            string = f"{string} ({adder_str})"

        return f"{string}{modifier_str}"

    def get_primary_forward(self, active_hero: Optional['Hero'] = None) -> float:
        """Get primary forward movement."""
        self._calc_primary_forward(active_hero)
        return self.primary_forward
    
    def _calc_primary_forward(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate primary forward movement."""
        # Imported here, not at module scope: the TYPE_CHECKING import
        # above is invisible at runtime, and this is used in an
        # isinstance() check — NameError the moment the method runs.
        # Unreachable until the loader began building Leaping objects.
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.objects.powers.power import Power

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
        # Imported here, not at module scope: the TYPE_CHECKING import
        # above is invisible at runtime, and this is used in an
        # isinstance() check — NameError the moment the method runs.
        # Unreachable until the loader began building Leaping objects.
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.objects.powers.power import Power

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
        # Imported here, not at module scope: the TYPE_CHECKING import
        # above is invisible at runtime, and this is used in an
        # isinstance() check — NameError the moment the method runs.
        # Unreachable until the loader began building Leaping objects.
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.objects.powers.power import Power

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
        # Imported here, not at module scope: the TYPE_CHECKING import
        # above is invisible at runtime, and this is used in an
        # isinstance() check — NameError the moment the method runs.
        # Unreachable until the loader began building Leaping objects.
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.objects.powers.power import Power

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


def _active_hero():
    """The character these distances are relative to.

    A leap is the CHARACTER's, not the characteristic's: the calculators walk
    the hero's powers for LEAPING contributions. With no hero they return the
    bare characteristic and the readout is wrong rather than absent.
    """
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
