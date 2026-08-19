"""
Characteristic base class for kirby-cost.

Converted from com.hero.objects.characteristics.Characteristic.java

This is the base class for all characteristics (STR, DEX, CON, etc.).
"""

from typing import Optional, List, Dict, TYPE_CHECKING
from copy import copy

from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_down, round_half_up, round_down
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.objects.frameworks import is_multipower, is_elemental_control, is_vpp
from kirby_cost.objects.modifiers.linked import is_linked

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.objects.modifier import Modifier
    from kirby_cost.objects.adder import Adder
    from kirby_cost.objects.frameworks.multipower import Multipower
    from kirby_cost.objects.frameworks.elemental_control import ElementalControl
    from kirby_cost.objects.frameworks.vpp import VariablePowerPool
    from kirby_cost.objects.powers.compound_power import CompoundPower
    from kirby_cost.objects.powers.automaton import Automaton


class Characteristic(CharAffectingObject):
    """
    Base class for all characteristics.
    
    Characteristics can be:
    - Base characteristics (STR, DEX, CON, etc.)
    - Power-based characteristics (purchased as powers)
    - Equipment-based characteristics
    
    Handles:
    - Base value calculations (including figured characteristics)
    - Primary/secondary value calculations
    - NCM (Normal Characteristic Maxima) calculations
    - Modifier application to base characteristics
    """
    
    def __init__(self, xmlid: str = "CHARACTERISTIC"):
        """Initialize a Characteristic."""
        super().__init__()
        self.xmlid = xmlid
        self.affects_primary = True
        
        # Modifier application
        self._add_modifiers_to_base: bool = False
        self.assigned_mods: List['Modifier'] = []

        # Base value calculations
        self.base_level: float = 0.0
        self.base_value: float = 0.0
        self.double_base: float = 0.0
        self.orig_base_level: float = 0.0

        # Figured minimum value
        self.figured_min_value: float = 0.0

        # Maximum value
        self.max_val: int = 999

        # NCM (Normal Characteristic Maxima)
        self.ncm_char_value: float = 0.0
        self.ncm_levels: Dict[str, int] = {}

        # Primary/secondary values
        self.primary_value: float = 0.0
        self.secondary_value: float = 0.0
        
        # Display
        self.show_roll: bool = True
        
        # Default values
        self._duration = "PERSISTENT"
        self.target = "SELFONLY"
        if "STANDARD" not in self._types:
            self._types.append("STANDARD")

        # Hero reference (set by loader for addModifiersToBase)
        self._hero = None

        # Apply 6E default costs based on XMLID
        self._apply_6e_defaults(xmlid)
    
    # 6E characteristic defaults: levelCost, levelValue per XMLID
    _6E_DEFAULTS = {
        "STR": (1.0, 1.0), "DEX": (2.0, 1.0), "CON": (1.0, 1.0),
        "INT": (1.0, 1.0), "EGO": (1.0, 1.0), "PRE": (1.0, 1.0),
        "OCV": (5.0, 1.0), "DCV": (5.0, 1.0),
        "OMCV": (3.0, 1.0), "DMCV": (3.0, 1.0),
        "PD": (1.0, 1.0), "ED": (1.0, 1.0),
        "SPD": (10.0, 1.0), "REC": (1.0, 1.0),
        "END": (1.0, 5.0), "BODY": (1.0, 1.0), "STUN": (1.0, 2.0),
        "RUNNING": (1.0, 1.0), "SWIMMING": (1.0, 2.0), "LEAPING": (1.0, 2.0),
        "COM": (1.0, 2.0), "SIZE": (15.0, 1.0),
    }

    # 6E power-level costs for characteristics when purchased as powers
    # (e.g., inside a CompoundPower).  These are the costs from the Java
    # template's characteristic entries, which differ from the base
    # characteristic costs for PD and ED.
    _6E_POWER_DEFAULTS = {
        "PD": (3.0, 2.0), "ED": (3.0, 2.0),
    }

    def _apply_6e_defaults(self, xmlid: str) -> None:
        """Apply 6E default level cost and level value for a characteristic."""
        defaults = self._6E_DEFAULTS.get(xmlid.upper())
        if defaults:
            self._level_cost, self._level_value = defaults

    def apply_power_costs(self) -> None:
        """Apply 6E power-level costs for characteristics purchased as powers.

        In Java, the template has different costs for PD/ED when purchased as
        powers (lc=3, lv=2) vs as base characteristics (lc=1, lv=1).  This
        method upgrades to the power costs when the characteristic is used as
        a power (e.g., inside a CompoundPower).
        """
        power_defaults = self._6E_POWER_DEFAULTS.get(self.xmlid.upper())
        if power_defaults:
            self._level_cost, self._level_value = power_defaults

    @property
    def add_modifiers_to_base(self) -> bool:
        """Whether modifiers should be added to base characteristic."""
        if not self.is_power:
            return False
        return self._add_modifiers_to_base

    @add_modifiers_to_base.setter
    def add_modifiers_to_base(self, value: bool) -> None:
        self._add_modifiers_to_base = value
    
    @property
    def type(self) -> int:
        """Get the characteristic type (to be overridden by subclasses)."""
        # Map XMLID to type
        type_map = {
            'STR': 1, 'DEX': 2, 'CON': 3, 'INT': 4, 'EGO': 5, 'PRE': 6,
            'OCV': 7, 'DCV': 8, 'OMCV': 9, 'DMCV': 10, 'SPD': 11,
            'PD': 12, 'ED': 13, 'REC': 14, 'END': 15, 'BODY': 16, 'STUN': 17,
            'RUNNING': 18, 'SWIMMING': 19, 'LEAPING': 20
        }
        return type_map.get(self.xmlid, 0)
    
    @property
    def true_base(self) -> float:
        """Get the true base level (original base level)."""
        return self.orig_base_level
    
    def get_base_value(self, active_hero: Optional['Hero'] = None) -> float:
        """
        Get the base value (cached).

        Args:
            active_hero: Optional active hero for calculations

        Returns:
            Base value
        """
        self._calc_base_value(active_hero)
        return self.base_value
    
    def _calc_base_value(self, active_hero: Optional['Hero'] = None) -> None:
        """
        Calculate the base value.

        This includes contributions from other characteristics and powers.
        """
        from kirby_cost.objects.powers.compound_power import CompoundPower
        d = 0.0
        self.double_base = self.base_level

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
            
            # Check equipment (similar logic to powers)
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
    
    def characteristic_value(self, active_hero: Optional['Hero'] = None) -> float:
        """
        Get the characteristic value (base + levels).
        
        Args:
            active_hero: Optional active hero for calculations
            
        Returns:
            Characteristic value
        """
        d = 0.0
        if not self.is_power:
            d = self.get_base_value(active_hero) + float(self._levels)
        else:
            d = self.get_base_value(active_hero)
            if active_hero is not None:
                base_char = active_hero.characteristic(self.type)
                if base_char is not None:
                    d += float(base_char.levels)
        
        if d < float(self._minimum_level):
            return float(self._minimum_level)
        if d > float(self.max_val):
            return float(self.max_val)
        return d
    
    def get_primary_value(self, active_hero: Optional['Hero'] = None) -> float:
        """
        Get the primary value (cached).
        
        Args:
            active_hero: Optional active hero for calculations
            
        Returns:
            Primary value
        """
        self._calc_primary_value(active_hero)
        return self.primary_value
    
    def _calc_primary_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate the primary value."""
        from kirby_cost.objects.powers.compound_power import CompoundPower
        d2 = self.characteristic_value(active_hero)
        
        if self.is_power and active_hero is not None:
            for char_obj in active_hero.characteristics:
                if char_obj.xmlid == self.xmlid:
                    self.double_base += float(char_obj.levels)
        
        if active_hero is not None:
            # Check powers
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    if isinstance(power, Characteristic):
                        char_obj = power
                        if char_obj.affect_primary and char_obj.affect_total:
                            d2 += float(char_obj.levels)
                            self.double_base += float(char_obj.levels)
                    continue
                
                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if sub_power.xmlid == self.xmlid:
                            if isinstance(sub_power, Characteristic):
                                char_obj = sub_power
                                if char_obj.affect_primary and char_obj.affect_total:
                                    d2 += float(char_obj.levels)
                                    self.double_base += float(char_obj.levels)
                        elif isinstance(sub_power, CharAffectingObject):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                not char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d = char_obj.increase_value(self.type, True)
                            self.double_base += d
                            d2 += round_half_up(d)
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
                    d2 += round_half_up(d3)
            
            # Check equipment (similar logic)
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    if isinstance(equip, Characteristic):
                        char_obj = equip
                        if char_obj.affect_primary and char_obj.affect_total:
                            d2 += float(char_obj.levels)
                            self.double_base += float(char_obj.levels)
                    continue
                
                if isinstance(equip, CompoundPower):
                    for sub_power in equip.powers:
                        if sub_power.xmlid == self.xmlid:
                            if isinstance(sub_power, Characteristic):
                                char_obj = sub_power
                                if char_obj.affect_primary and char_obj.affect_total:
                                    d2 += float(char_obj.levels)
                                    self.double_base += float(char_obj.levels)
                        elif isinstance(sub_power, CharAffectingObject):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                char_obj.increase(self.type) == 0.0 or
                                not char_obj.affect_primary or
                                not CharAffectingObject.check_figured(char_obj, self.type) or
                                not char_obj.affect_total):
                                continue
                            d = char_obj.increase_value(self.type, True)
                            self.double_base += d
                            d2 += round_half_up(d)
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
                    d2 += round_half_up(d4)
        
        self.primary_value = d2
    
    def get_secondary_value(self, active_hero: Optional['Hero'] = None) -> float:
        """
        Get the secondary value (cached).
        
        Args:
            active_hero: Optional active hero for calculations
            
        Returns:
            Secondary value
        """
        self._calc_secondary_value(active_hero)
        return self.secondary_value
    
    def _calc_secondary_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate the secondary value."""
        from kirby_cost.objects.powers.compound_power import CompoundPower
        d2 = 0.0

        if active_hero is not None:
            # Check powers
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    if isinstance(power, Characteristic):
                        char_obj = power
                        if not char_obj.affect_primary and char_obj.affect_total:
                            d2 += float(char_obj.levels)
                    continue

                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if sub_power.xmlid == self.xmlid:
                            if isinstance(sub_power, Characteristic):
                                char_obj = sub_power
                                if not char_obj.affect_primary and char_obj.affect_total:
                                    d2 += float(char_obj.levels)
                        elif isinstance(sub_power, CharAffectingObject):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                not CharAffectingObject.check_figured(char_obj, self.type)):
                                continue
                            d = char_obj.increase_value(self.type, False)
                            d2 += round_half_up(d)
                elif isinstance(power, CharAffectingObject):
                    char_obj = power
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d3 = char_obj.increase_value(self.type, False)
                    d2 += round_half_up(d3)
            
            # Check equipment (similar logic)
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    if isinstance(equip, Characteristic):
                        char_obj = equip
                        if not char_obj.affect_primary and char_obj.affect_total:
                            d2 += float(char_obj.levels)
                    continue
                
                if isinstance(equip, CompoundPower):
                    for sub_power in equip.powers:
                        if sub_power.xmlid == self.xmlid:
                            if isinstance(sub_power, Characteristic):
                                char_obj = sub_power
                                if not char_obj.affect_primary and char_obj.affect_total:
                                    d2 += float(char_obj.levels)
                        elif isinstance(sub_power, CharAffectingObject):
                            char_obj = sub_power
                            if (char_obj.increase_levels(self.type) <= 0 or
                                not CharAffectingObject.check_figured(char_obj, self.type)):
                                continue
                            d = char_obj.increase_value(self.type, False)
                            d2 += round_half_up(d)
                elif isinstance(equip, CharAffectingObject):
                    char_obj = equip
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d4 = char_obj.increase_value(self.type, False)
                    d2 += round_half_up(d4)
        
        self.secondary_value = min(self.get_primary_value(active_hero) + d2, float(self.max_val))
    
    def value_display(self, active_hero: Optional['Hero'] = None) -> str:
        """Get the value display string."""
        primary = self.get_primary_value(active_hero)
        secondary = self.get_secondary_value(active_hero)
        if primary != secondary:
            return f"{round_half_up(primary)}/{round_half_up(secondary)}"
        return str(round_half_up(primary))
    
    def characteristic_base(self, active_hero: Optional['Hero'] = None) -> str:
        """Get the base value as a string."""
        return str(round_half_up(self.get_base_value(active_hero)))
    
    def figured(self, active_hero: Optional['Hero'] = None) -> bool:
        """Check if this characteristic is figured."""
        if active_hero is None:
            return False
        
        for char in active_hero.characteristics:
            if (char.increase(self.type) > 0.0 and
                char.increase_levels(self.type) > 0):
                return True
        return False
    
    @property
    def is_power(self) -> bool:
        """
        Check if this is a power (not a base characteristic).

        Overrides GenericObject.is_power to add characteristic-specific logic.
        Uses self._hero (wired by HDCLoader._wire_hero_reference).
        """
        # Check the internal attribute first
        if self._is_power:
            return True

        active_hero = self._hero
        if active_hero is None:
            return self._is_power

        # Check if this characteristic exists in the hero's characteristics list
        chars = getattr(active_hero, 'characteristics', [])
        for char_obj in chars:
            if char_obj._id == self._id:
                return False

        return True
    
    @property
    def minimum_level(self) -> int:
        """Get minimum level (0 for powers)."""
        if self.is_power:
            return 0
        return super().minimum_level

    @minimum_level.setter
    def minimum_level(self, value) -> None:
        self._minimum_level = value
    
    @property
    def min_levels(self) -> float:
        """Get minimum levels (negative of base value for non-powers)."""
        if self.is_power:
            return 0.0
        return 0.0 - self.get_base_value()
    
    def set_value(self, value: float, active_hero: Optional['Hero'] = None) -> None:
        """Set the characteristic value by adjusting levels."""
        current_value = self.characteristic_value(active_hero)
        base = self.get_base_value(active_hero)
        
        if value == current_value:
            return
        
        if value < float(self._minimum_level):
            self._levels = int(round_half_down(float(self._minimum_level - base)))
        elif value < float(self.max_val):
            self._levels = int(round_half_down(value - base))
        else:
            self._levels = int(round_half_down(float(self.max_val - base)))
    
    def roll(self, active_hero: Optional['Hero'] = None) -> str:
        """Get the roll string (e.g., "11-", "12-/14-")."""
        if not self.show_roll:
            return ""
        
        n = 9  # Default base
        d = 5.0  # Default denominator
        
        if active_hero is not None and active_hero.rules is not None:
            n = active_hero.rules.char_roll_base
            d = active_hero.rules.char_roll_denominator
        
        primary = self.get_primary_value(active_hero)
        secondary = self.get_secondary_value(active_hero)
        
        n3 = int(n + round_half_up(primary / d))
        n2 = int(n + round_half_up(secondary / d))
        
        if n3 != n2:
            return f"{n3}- / {n2}-"
        return f"{n3}-"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for base characteristic)."""
        return ""
    
    @property
    def display_notes(self) -> str:
        """Get display notes (empty for base characteristic)."""
        return ""
    
    def ap_per_end(self, active_hero: Optional['Hero'] = None) -> int:
        """
        Get Active Points per END cost.
        
        For characteristics, this typically comes from rules.
        Default is 10 for 6E (1 END per 10 Active Points).
        For STR, uses STR AP per END (default 5).
        """
        n = 10  # Default for 6E
        
        if active_hero is not None and active_hero.rules is not None:
            n = active_hero.rules.ap_per_end
            # STR uses different AP per END
            if self.xmlid == "STR":
                n = active_hero.rules.str_ap_per_end
        
        # Check if this uses END
        if not self.uses_end:
            return 0
        
        return n
    
    def orig_ap_per_end(self, active_hero: Optional['Hero'] = None) -> int:
        """
        Get original AP per END (before modifiers).
        
        For characteristics, this is the same as get_ap_per_end().
        """
        n = 10  # Default for 6E
        
        if active_hero is not None and active_hero.rules is not None:
            n = active_hero.rules.ap_per_end
            # STR uses different AP per END
            if self.xmlid == "STR":
                n = active_hero.rules.str_ap_per_end
        
        # Check if this uses END
        if not self.uses_end:
            n = 0
        
        return n
    

    def _modifiers_borrowed_from_powers(self) -> list:
        """Modifiers this characteristic shows but did not buy.

        Ported from ``Characteristic.calcAssignedModifiers``
        (Characteristic.java:120). A character who buys "+12 ED" and then buys
        Hardened ED as a POWER with ``ADD_MODIFIERS_TO_BASE="Yes"`` has one
        defence, not two, and HD says so: the base characteristic prints
        "+12 ED, Hardened (+1/4), Resistant (+1/2)" while the power that
        carries those modifiers prints separately.

        HD searches POWERS and EQUIPMENT, and looks inside CompoundPowers,
        for a Characteristic with the same XMLID, a DIFFERENT id, and the
        flag set. Matching on xmlid alone would make a characteristic borrow
        from itself.

        DISPLAY ONLY, deliberately. Java merges these into
        ``getAssignedModifiers()``, which the cost chain also reads — but the
        oracle prices this ED at 12 points, not at 12 x 1.75, so the merged
        advantages do not reach its cost. Rather than reproduce that by
        changing the list every cost path reads and hoping, the borrowed
        modifiers are handed to the display and to nothing else.
        """
        if self._is_power:
            return []
        hero = _active_hero()
        if hero is None:
            return []

        borrowed: list = []
        mine = self._assigned_modifiers

        def consider(obj):
            if not isinstance(obj, Characteristic):
                return
            if obj.xmlid != self.xmlid or obj._id == self._id:
                return
            if not obj.add_modifiers_to_base:
                return
            for mod in obj.assigned_modifiers:
                if (GenericObject.find_object_by_id(mine, mod.xmlid) is None
                        and GenericObject.find_object_by_id(borrowed, mod.xmlid) is None):
                    borrowed.append(mod)

        for group in (getattr(hero, "powers", None) or (),
                      getattr(hero, "equipment", None) or ()):
            for obj in group:
                consider(obj)
                for sub in (getattr(obj, "powers", None) or ()):
                    consider(sub)
        return borrowed

    @property
    def modifier_string(self) -> str:
        """As GenericObject's, plus whatever this characteristic borrows."""
        borrowed = self._modifiers_borrowed_from_powers()
        if not borrowed:
            return super().modifier_string
        original = self._assigned_modifiers
        self._assigned_modifiers = list(original) + borrowed
        try:
            return super().modifier_string
        finally:
            self._assigned_modifiers = original

    @property
    def column2_output(self) -> str:
        """What HD prints for this characteristic on the sheet.

        Ported from ``Characteristic.getColumn2Output``
        (Characteristic.java:1006). This class inherited GenericObject's
        default — the alias alone — so HD's ``+0 DEX`` came out as ``DEX``, on
        14,217 of the 27,354 objects whose display text disagreed with HD
        across the corpus. Half of the whole display gap was this one method.
        """
        levels = self.levels
        alias = self._alias or ""
        name = (self._name or "").strip()

        # A characteristic bought at no levels purely to carry modifiers reads
        # the other way round: the modifiers are the subject and the
        # characteristic is what they are applied TO. HD strips the leading
        # comma that modifier_string always carries.
        if levels == 0 and self.add_modifiers_to_base:
            mods = (self.modifier_string or "").strip()
            if mods:
                if mods.startswith(","):
                    mods = mods[1:].strip()
                mods += f" applied to {alias}"
                if name:
                    mods = f"<i>{name}:</i>  {mods}"
                return mods

        ret = "+" if levels >= 0 else ""
        if name:
            ret = f"<i>{name}:</i>  {ret}"
        ret += f"{levels} {alias}"

        if self.input and self.input.strip():
            ret += f":  {self.input}"

        adders = (self.adder_string or "").strip()
        option = self._selected_option
        if option is not None:
            ret += f" ({option.alias or ''}"
            if adders:
                ret += f"; {adders}"
            ret += ")"
        elif adders:
            ret += f" ({adders})"

        ret += self.modifier_string or ""

        # Only when the character actually HAS an Endurance Reserve to draw
        # on — HD looks it up on the active hero rather than assuming.
        # `end_usage` is a METHOD here and a PROPERTY on GenericObject — this
        # class overrides one with the other. Reading it without the call
        # compares a bound method to an int and raises.
        if self.end_usage > 0 and not _use_wg():
            if (_active_hero_has_endurance_reserve()
                    and GenericObject.find_object_by_id(
                        self.assigned_modifiers, "ENDRESERVEOREND") is None):
                ret += (" (uses END Reserve)" if self.use_end_reserve
                        else " (uses Personal END)")

        if self.add_modifiers_to_base:
            ret += " (Modifiers affect Base Characteristic)"

        return ret

    # ═══════════════════════════════════════════════════════════
    #  Cost calculations — ported from Characteristic.java
    # ═══════════════════════════════════════════════════════════

    @property
    def total_cost(self) -> float:
        """
        Calculate total cost for a characteristic.

        Differs from GenericObject.total_cost:
        - Uses levels/levelValue * levelCost directly (no floor/ceil)
        - Adds NCM doubling cost for 6E
        - Splits adders into positive (before clamp) and negative (after clamp)
        - Automaton defense multiplier

        Ported from Characteristic.java getTotalCost().
        """
        self.enhancer_applied = None
        d = self.base_cost

        # Level cost: levels / levelValue * levelCost (no floor/ceil rounding)
        if self._level_value != 0.0:
            d += float(self._levels) / self._level_value * self._level_cost

        # NCM (Normal Characteristic Maxima) doubling cost
        # In 6E, if characteristic exceeds NCM level, excess costs double
        if self.is_power:
            pass  # Power-based characteristics don't get NCM doubling
        else:
            ncm_cost_multiplier = self._get_ncm_cost_multiplier()
            if ncm_cost_multiplier > 0:
                ncm_char_value = self.get_ncm_char_value()
                ncm_level = self.ncm_level()
                if ncm_char_value > ncm_level:
                    excess = ncm_char_value - ncm_level
                    true_base = self.orig_base_level
                    levels = self._levels
                    if excess > levels and true_base < ncm_level:
                        excess = float(levels)
                    if self._level_value != 0.0:
                        d += excess / self._level_value * self._level_cost * (ncm_cost_multiplier - 1)

        # Positive adders (before min/max clamp)
        for adder in self.assigned_adders:
            if adder.real_cost > 0.0:
                d += adder.real_cost

        # Min/max clamp
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        elif d > self._max_cost and self.max_set:
            d = self._max_cost

        # Negative adders (after clamp)
        for adder in self.assigned_adders:
            if adder.real_cost < 0.0:
                d += adder.real_cost

        # Automaton defense multiplier
        # When a character has Automaton (Takes No STUN), PD/ED costs are multiplied
        # This applies to both characteristic-section and power-section PD/ED
        if self.xmlid in ("PD", "ED") and self._hero is not None:
            multiplier = self._get_automaton_defense_multiplier()
            if multiplier > 1:
                d *= multiplier

        return d

    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""
        return self._compute_active_cost()



    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """
        Calculate active cost for a characteristic.

        Non-power characteristics: active cost = total cost (no advantages apply).
        Power-based characteristics: standard advantage calculation with
        optional addModifiersToBase handling.

        Ported from Characteristic.java getActiveCost().
        """
        total = self.total_cost

        if not self.is_power:
            return total

        # Power-based characteristic: standard advantage logic
        modifier_sum = 0.0
        has_advantages = False

        for modifier in self.assigned_modifiers:
            modifier.parent = self
            if exclude_xmlid and modifier.xmlid == exclude_xmlid:
                continue
            if modifier.total_value > 0.0:
                modifier_sum += modifier.total_value
                has_advantages = True

        # Parent list advantages
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent

        if parent:
            for modifier in parent.assigned_modifiers:
                if modifier.types and "VPP" in modifier.types:
                    continue
                if modifier.xmlid == "CHARGES" and is_multipower(parent):
                    continue
                if is_linked(modifier):
                    continue
                if modifier.total_value <= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, modifier.xmlid) and
                    modifier.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                if is_multipower(parent) or is_elemental_control(parent):
                    continue
                modifier_sum += modifier.total_value
                has_advantages = True

        # addModifiersToBase contribution
        # When a power-based characteristic has addModifiersToBase=True,
        # advantages also apply to the BASE characteristic value (not just purchased levels).
        # This requires knowing the hero's total characteristic value.
        #
        # Java: Characteristic.getActiveCost() lines 401-409.
        # For DEFENSE types with Automaton NOSTUN, the base PD/ED level is divided
        # by basePDEDDenomenator (=defenseCostMultiplier, typically 3) before computing
        # the characteristic value, and then base_char_cost is multiplied by the same.
        d4 = 0.0
        if self.add_modifiers_to_base and modifier_sum > 0.0:
            char_value = 0.0
            if self._hero is not None and hasattr(self._hero, 'characteristic_value'):
                char_value = self._hero.characteristic_value(self.xmlid)
            elif self.orig_base_level > 0:
                char_value = self.orig_base_level
            if char_value > 0 and self._level_value != 0.0:
                base_char_cost = char_value * self._level_cost / self._level_value
                # Automaton NOSTUN defense multiplier: Java PhysicalDefense.calcBaseValue()
                # divides origBaseLevel by basePDEDDenomenator, then getActiveCost()
                # multiplies d6 by defenseCostMultiplier.  Net effect:
                # d6 = ((6e_base / denom) + levels) * lc/lv * denom
                if "DEFENSE" in self.types:
                    auto_mult = self._get_automaton_defense_multiplier()
                    if auto_mult > 1:
                        # Get 6E base value for this characteristic
                        _6e_bases = {"PD": 2, "ED": 2}
                        base_6e = _6e_bases.get(self.xmlid, 0)
                        char_levels = char_value - base_6e
                        adjusted = (base_6e / auto_mult) + char_levels
                        base_char_cost = adjusted * self._level_cost / self._level_value * auto_mult
                d4 = round_half_down(base_char_cost * (1.0 + modifier_sum) - base_char_cost)

        active_cost = total * (1.0 + modifier_sum)

        if has_advantages:
            active_cost = round_half_down(active_cost)
            if total > 0.0 and active_cost < 1.0:
                active_cost = 1.0

        return active_cost + d4

    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost for a characteristic.

        Non-power characteristics: real cost = active cost (no limitations apply).
        Power-based characteristics: standard limitation calculation with
        optional addModifiersToBase handling.

        Ported from Characteristic.java getRealCostPreList().
        """
        active_cost = self.active_cost

        if not self.is_power:
            return active_cost

        # Power-based characteristic: standard limitation logic
        self.enhancer_applied = None
        limitation_sum = 0.0
        has_limitations = False

        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += modifier.total_value
                has_limitations = True

        # Parent list limitations
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent

        if parent and not is_vpp(parent):
            for modifier in parent.assigned_modifiers:
                if modifier.types and "VPP" in modifier.types:
                    continue
                if modifier.xmlid == "CHARGES" and is_multipower(self._parent):
                    continue
                if modifier.total_value >= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, modifier.xmlid) and
                    modifier.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                limitation_sum += modifier.total_value
                has_limitations = True

        # addModifiersToBase limitation savings
        # Java: Characteristic.getRealCostPreList() lines 992-1002.
        # Same Automaton NOSTUN adjustment as in getActiveCost().
        d3 = 0.0
        if self.add_modifiers_to_base and limitation_sum != 0.0:
            char_value = 0.0
            if self._hero is not None and hasattr(self._hero, 'characteristic_value'):
                char_value = self._hero.characteristic_value(self.xmlid)
            elif self.orig_base_level > 0:
                char_value = self.orig_base_level
            if char_value > 0 and self._level_value != 0.0:
                base_char_cost = char_value * self._level_cost / self._level_value
                # Automaton NOSTUN defense multiplier (same as get_active_cost)
                if "DEFENSE" in self.types:
                    auto_mult = self._get_automaton_defense_multiplier()
                    if auto_mult > 1:
                        _6e_bases = {"PD": 2, "ED": 2}
                        base_6e = _6e_bases.get(self.xmlid, 0)
                        char_levels = char_value - base_6e
                        adjusted = (base_6e / auto_mult) + char_levels
                        base_char_cost = adjusted * self._level_cost / self._level_value * auto_mult
                lim_savings = base_char_cost - base_char_cost / (1.0 + abs(limitation_sum))
                d3 = round_half_down(lim_savings)

        real_cost = active_cost / (1.0 + abs(limitation_sum))
        if has_limitations:
            real_cost = round_half_down(real_cost)

        # Minimum 1 CP
        if (real_cost < 1.0 and
            (active_cost > 0.0 or
             (self._levels > 0 and len(self.assigned_adders) == 0 and
              self.base_cost >= 0.0))):
            real_cost = 1.0

        real_cost -= d3  # Subtract base limitation savings

        # Quantity cost
        if self._quantity > 1:
            quantity_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                quantity_cost += 5
                qty /= 2.0
            real_cost += float(quantity_cost)

        return real_cost

    def _get_automaton_defense_multiplier(self) -> int:
        """
        Get the defense cost multiplier from Automaton power.

        When a character has Automaton (Takes No STUN), PD and ED costs
        are multiplied by the Automaton's defense_cost_multiplier (typically 3).
        Returns 1 if no Automaton or not a NOSTUN variant.
        """
        if self._hero is None:
            return 1
        # Search hero's powers for Automaton
        from kirby_cost.objects.powers.automaton import Automaton
        powers = getattr(self._hero, 'powers', [])
        for p in powers:
            if isinstance(p, Automaton):
                option_id = getattr(p, 'option_id', '')
                if option_id and option_id.upper().startswith("NOSTUN"):
                    return p.defense_cost_multiplier
        return 1

    def _get_ncm_cost_multiplier(self) -> int:
        """
        Get the NCM cost multiplier from rules.

        In 6E, characteristics above NCM cost double (multiplier=2).
        Returns 0 if NCM is not in effect.
        """
        # For 6E, NCM is always in effect with multiplier 2
        # This would need rules/template access for full implementation
        # Default to 6E behavior: NCM multiplier = 2
        # But only if NCM is selected — for now return 0 (disabled)
        # since we need rules integration to know if NCM applies
        return 0

    @property
    def end_usage(self) -> int:
        """
        Get END usage for this characteristic.
        
        For most characteristics, this is 0 unless they're purchased as powers.
        """
        # Most characteristics don't cost END
        # This would be overridden for movement characteristics
        return 0
    
    def figured_base_value(self, char_type: int, active_hero: Optional['Hero'] = None) -> float:
        """
        Get figured base value for a characteristic type.
        
        This is used for calculating figured characteristics.
        Similar to calc_base_value but uses figured values.
        """
        d = 0.0
        self.double_base = self.orig_base_level
        
        if active_hero is not None:
            # Check characteristics
            for char_obj in active_hero.characteristics:
                if (char_obj.xmlid == self.xmlid or
                    char_obj.increase_levels(self.type) <= 0 or
                    char_obj.increase(self.type) == 0.0 or
                    not CharAffectingObject.check_figured(char_obj, self.type)):
                    continue
                
                if isinstance(char_obj, Characteristic):
                    char_value = char_obj.characteristic_value(active_hero)
                    increase = char_obj.increase(self.type)
                    increase_levels = char_obj.increase_levels(self.type)
                    d2 = char_value * increase / float(increase_levels)
                    self.double_base += d2
                    d += round_half_up(d2)
            
            # Check powers
            for power in active_hero.powers:
                if power.xmlid == self.xmlid:
                    if isinstance(power, Characteristic):
                        char_obj = power
                        if (char_obj.affect_primary and
                            char_obj.affect_total and
                            CharAffectingObject.check_figured(char_obj, char_type)):
                            d += float(char_obj.levels)
                    continue
                
                if isinstance(power, CharAffectingObject):
                    char_obj = power
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not char_obj.affect_primary or
                        not char_obj.affect_total or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d2 = char_obj.increase_value(self.type, True)
                    self.double_base += d2
                    d += round_half_up(d2)
            
            # Check equipment (similar logic)
            for equip in active_hero.equipment:
                if equip.xmlid == self.xmlid:
                    if isinstance(equip, Characteristic):
                        char_obj = equip
                        if (char_obj.affect_primary and
                            char_obj.affect_total and
                            CharAffectingObject.check_figured(char_obj, char_type)):
                            d += float(char_obj.levels)
                    continue
                
                if isinstance(equip, CharAffectingObject):
                    char_obj = equip
                    if (char_obj.increase_levels(self.type) <= 0 or
                        not char_obj.affect_primary or
                        not char_obj.affect_total or
                        not CharAffectingObject.check_figured(char_obj, self.type)):
                        continue
                    d2 = char_obj.increase_value(self.type, True)
                    self.double_base += d2
                    d += round_half_up(d2)
        
        if self.base_level + d < float(self.max_val):
            return self.base_level + d
        return float(self.max_val)
    
    def get_figured_min_value(self, active_hero: Optional['Hero'] = None) -> float:
        """Get figured minimum value."""
        self._calc_figured_min_value(active_hero)
        return self.figured_min_value

    def _calc_figured_min_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate figured minimum value."""
        # Similar to calc_base_value but for minimum
        # This is a simplified version - full implementation would mirror Java
        self.figured_min_value = self.get_base_value(active_hero)

    def get_ncm_char_value(self, active_hero: Optional['Hero'] = None) -> float:
        """Get NCM (Normal Characteristic Maxima) characteristic value."""
        self._calc_ncm_char_value(active_hero)
        return self.ncm_char_value
    
    def _calc_ncm_char_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate NCM characteristic value."""
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
                    d += round_half_up(d2)
        self.ncm_char_value = min(d, float(self.max_val))
    
    def ncm_level(self, active_hero: Optional['Hero'] = None) -> int:
        """Get NCM level (stub - needs template/rules integration)."""
        # This would check template and rules for NCM settings
        # For now, return a high value (effectively no limit)
        return 9999
    
    def pre_increase_value(self, active_hero: Optional['Hero'] = None) -> float:
        """Get PRE increase value (for Presence characteristic)."""
        if (self.increase_levels(CharacteristicType.PRE) > 0 and
            self.increase(CharacteristicType.PRE) != 0.0):
            return (self.characteristic_value(active_hero) *
                   self.increase(CharacteristicType.PRE) /
                   float(self.increase_levels(CharacteristicType.PRE)))
        return 0.0
    
    def dcv_effect(self, primary: bool, active_hero: Optional['Hero'] = None) -> int:
        """Get DCV effect (for Dexterity characteristic)."""
        if self.dcv_increase_levels != 0:
            n = -1 if self.dcv_increase < 0.0 else 1
            d = 0.0
            d2 = self.get_primary_value(active_hero) if primary else self.get_secondary_value(active_hero)
            d = abs(self.dcv_increase) * d2 / float(self.dcv_increase_levels)
            d *= float(n)
            d = round_half_up(d)
            return int(d)
        return 0
    
    def get_value(self, figured: bool, char_type: int, active_hero: Optional['Hero'] = None) -> float:
        """
        Get value (figured or base).
        
        Args:
            figured: Whether to use figured base value
            char_type: Characteristic type
            active_hero: Optional active hero for calculations
            
        Returns:
            Characteristic value
        """
        d = self.figured_base_value(char_type, active_hero) if figured else self.get_base_value(active_hero)
        if d + float(self._levels) < float(self._minimum_level):
            self._levels = int(round_half_down(float(self._minimum_level - d)))
            return float(self._minimum_level)
        if d + float(self._levels) < float(self.max_val):
            return d + float(self._levels)
        self._levels = int(round_half_down(float(self.max_val - d)))
        return float(self.max_val)
    
    def get_save_xml(self):
        """
        Get XML element for saving this characteristic.
        
        Converted from com.hero.objects.characteristics.Characteristic.getSaveXML()
        
        Returns:
            lxml.etree.Element representing this characteristic's saved state
        """
        # Get base element from parent
        element = self.get_general_save_xml()
        
        # Set tag name to XMLID (e.g., "STR", "DEX", "CON")
        from lxml import etree
        element.tag = self.xmlid
        
        # Characteristic-specific attributes
        element.set("AFFECTS_PRIMARY", "Yes" if self.affect_primary else "No")
        element.set("AFFECTS_TOTAL", "Yes" if self.affect_total else "No")
        
        # Power-specific attributes
        if self.is_power:
            if self._use_end_reserve:
                element.set("USE_END_RESERVE", "Yes")
            element.set("ADD_MODIFIERS_TO_BASE", "Yes" if self._add_modifiers_to_base else "No")
        
        return element
    
    # Additional methods will be added in subsequent updates
    # This is a large class with many methods, so we'll build it incrementally


def _use_wg() -> bool:
    """The Writers Guide preference, defaulting to off when none is loaded."""
    try:
        from kirby_cost.core.context import EngineContext
        return bool(EngineContext.prefs().use_wg)
    except Exception:  # noqa: BLE001 — a missing preference is not an error here
        return False


def _active_hero_has_endurance_reserve() -> bool:
    """Whether the active hero carries an ENDURANCERESERVE power.

    HD reads this off the ACTIVE hero, so it is global state, and global state
    is what produced this project's longest-running divergences. Kept narrow
    and failing closed: no hero, no reserve, no note.
    """
    try:
        from kirby_cost.core.context import EngineContext
        hero = EngineContext.active_hero()
        if hero is None:
            return False
        return GenericObject.find_object_by_id(
            getattr(hero, "powers", []) or [], "ENDURANCERESERVE") is not None
    except Exception:  # noqa: BLE001
        return False


def _active_hero():
    """The character whose powers this characteristic may borrow from."""
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
