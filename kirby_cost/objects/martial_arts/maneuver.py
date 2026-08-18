"""
Martial Arts Maneuver.

Converted from com.hero.objects.martialarts.Maneuver.java

Represents a single martial arts maneuver (Block, Dodge, Strike, Kick, Throw, etc.).
All specific maneuvers are instances of this class with different configurations.
"""

from typing import Optional
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.martial_arts.extra_damage_classes import ExtraDamageClasses
from kirby_cost.objects.martial_arts.ranged_damage_classes import RangedDamageClasses
from kirby_cost.core.context import EngineContext
from kirby_cost.util.rounder import round_down, round_half_down
from kirby_cost.io.xml_utility import XMLUtility
from kirby_cost.objects.frameworks import is_multipower


class Maneuver(GenericObject, xmlid="MANEUVER"):
    """
    Martial Arts Maneuver.
    
    Represents a single martial arts maneuver with damage types,
    OCV/DCV modifiers, and effects. All specific maneuvers (Block, Dodge,
    Strike, Kick, Throw, etc.) are instances of this class with different
    configurations loaded from template files.
    """

    def to_build_dict(self) -> dict:
        d = super().to_build_dict()
        d["maneuver"] = True          # marker: re-emit a MANEUVER element tag
        d["category"] = self.category
        d["display"] = str(self.display or "")
        d["ocv"] = self.ocv
        d["dcv"] = self.dcv
        d["dc"] = int(self.dc)
        d["phase"] = self.phase
        d["effect"] = self.effect
        d["add_str"] = bool(self.add_str)
        d["maneuver_active_cost"] = int(self.maneuver_active_cost)
        d["damage_type"] = int(self.damage_type)
        d["max_str"] = int(self.max_str)
        d["str_multiplier"] = int(self.str_multiplier)
        d["use_weapon"] = bool(self.use_weapon)
        if self.custom:
            d["custom"] = True
        if self.weapon_effect and self.weapon_effect.strip():
            d["weapon_effect"] = self.weapon_effect
        if self.category.strip().upper() == "RANGED":
            d["ranged"] = int(self.ranged)
        return d

    
    # Damage type constants
    NONE = 0
    STR = 1
    NORMAL = 2
    KILLING = 3
    NND = 4
    FLASH = 5
    
    def __init__(self, element=None):
        """Initialize a Maneuver."""
        super().__init__()
        self.xmlid = "MANEUVER"
        self.damage_type: int = 0
        self.custom: bool = False
        self.ocv: str = "--"
        self.dcv: str = "--"
        self.phase: str = "1/2"
        self.effect: str = ""
        self.weapon_effect: str = ""
        self.ranged: int = 0
        self.category: str = "Hand To Hand"
        self._use_weapon: bool = False
        self.dcs: int = 0
        self.add_str: bool = False
        self._maneuver_active_cost: int = 0
        self.max_str: int = 0
        self.str_multiplier: int = 1
        
        if element is not None:
            self._init(element)
    
    @property
    def active_cost(self) -> float:
        """Get active cost (same as real cost for maneuvers)."""
        return self.real_cost_pre_list
    
    @property
    def real_cost_pre_list(self) -> float:
        """
        Get real cost before list modifiers.
        
        This is a complex calculation that:
        1. Temporarily sets base cost to effective active cost
        2. Calculates active cost with modifiers (excluding REDUCEDEND)
        3. Handles REDUCEDEND modifier specially
        4. Applies limitations
        5. Restores base cost
        6. Applies multiplier and quantity adjustments
        
        Converted from com.hero.objects.martialarts.Maneuver.getRealCostPreList()
        """
        # Save original base cost
        saved_base_cost = self.base_cost
        effective_active = self.effective_active_cost
        
        # Set base cost to effective active cost temporarily
        self.base_cost = effective_active
        
        cost = saved_base_cost  # Start with saved base cost
        
        if effective_active > 0.0:
            # Calculate active cost excluding REDUCEDEND
            active_with_mods = super()._compute_active_cost("REDUCEDEND")
            
            # Calculate the difference (modifier contribution)
            modifier_contribution = active_with_mods - effective_active
            
            # Add modifier contribution to base cost
            cost = saved_base_cost + modifier_contribution
            
            # Ensure cost doesn't go below original base cost
            if cost < saved_base_cost:
                cost = saved_base_cost
            
            # Collect all modifiers (including from parent list) for REDUCEDEND handling
            all_modifiers = list(self.assigned_modifiers)
            parent = self._parent
            if parent is None and self.main_power:
                parent = self.main_power.parent
            
            if parent:
                all_modifiers.extend(parent.assigned_modifiers)
            
            # Handle REDUCEDEND modifier specially
            reduced_end_mod = GenericObject.find_object_by_id(all_modifiers, "REDUCEDEND")
            if reduced_end_mod:
                # Calculate adjustment for REDUCEDEND
                adjustment = round_half_down(
                    (cost - saved_base_cost) * (1.0 + reduced_end_mod.total_value) - 
                    (cost - saved_base_cost)
                )
                cost += adjustment
            
            # Collect limitations (negative modifiers)
            limitation_sum = 0.0
            has_limitations = False
            
            # From assigned modifiers
            for modifier in self.assigned_modifiers:
                if modifier.total_value < 0.0:
                    limitation_sum += modifier.total_value  # Negative value
                    has_limitations = True
            
            # From parent list modifiers
            parent = self._parent
            if parent is None and self.main_power:
                parent = self.main_power.parent
            
            if parent:
                for modifier in parent.assigned_modifiers:
                    # Skip VPP modifiers
                    if modifier.types and "VPP" in modifier.types:
                        continue
                    # Skip CHARGES in Multipower
                    if (modifier.xmlid == "CHARGES" and 
                        is_multipower(self._parent)):
                        continue
                    # Skip if not a limitation
                    if modifier.total_value >= 0.0:
                        continue
                    # Skip if already assigned (unless generic)
                    if (GenericObject.find_object_by_id(self._assigned_modifiers, modifier.xmlid) and
                        modifier.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                        continue
                    
                    limitation_sum += modifier.total_value  # Negative value
                    has_limitations = True
            
            # Apply limitations
            if has_limitations:
                cost = cost / (1.0 + abs(limitation_sum))
                cost = round_half_down(cost)
            
            # Minimum cost check
            if cost < 1.0:
                cost = 1.0
        
        # Restore base cost
        self.base_cost = saved_base_cost
        
        # Apply multiplier if rules allow
        active_hero = EngineContext.active_hero()
        if active_hero and active_hero.rules and active_hero.rules.multiplier_allowed:
            if self.multiplier != 1.0:
                cost *= self.multiplier
                cost = round_half_down(cost)
            elif self._parent and self._parent.multiplier != 1.0:
                cost *= self._parent.multiplier
                cost = round_half_down(cost)
        
        # Apply quantity cost (5 points per doubling)
        if self._quantity > 1:
            quantity_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                quantity_cost += 5
                qty /= 2.0
            cost += float(quantity_cost)
        
        return cost
    
    @property
    def effective_active_cost(self) -> float:
        """
        Get effective active cost including STR and damage classes.
        
        Returns:
            Effective active cost
        """
        cost = float(self._maneuver_active_cost)
        
        # Add STR if applicable
        if self.add_str:
            active_hero = EngineContext.active_hero()
            if active_hero:
                str_char = active_hero.characteristic(1)  # STR
                if str_char:
                    str_val = str_char.get_secondary_value(active_hero)
                    if self.max_str > 0 and str_val > self.max_str:
                        str_val = self.max_str
                    cost += str_val * str_char.level_cost / str_char.level_value * self.str_multiplier
        
        # Add damage classes if applicable
        if self.does_damage:
            is_hth = self.category.strip().upper().startswith("HAND")
            active_hero = EngineContext.active_hero()
            if active_hero:
                for maneuver in active_hero.maneuvers:
                    if isinstance(maneuver, ExtraDamageClasses) and is_hth:
                        cost += maneuver.levels * 5.0
                    elif isinstance(maneuver, RangedDamageClasses) and not is_hth:
                        cost += maneuver.levels * 5.0
        
        if cost < 1.0:
            cost = 1.0
        
        return cost
    
    @property
    def maneuver_active_cost(self) -> int:
        """Get maneuver active cost."""
        return self._maneuver_active_cost

    @maneuver_active_cost.setter
    def maneuver_active_cost(self, cost: int) -> None:
        """Set maneuver active cost."""
        self._maneuver_active_cost = cost
    
    @staticmethod
    def fraction(value: float) -> str:
        """
        Convert decimal to fraction string (e.g., 0.25 -> "+1/4").
        
        Args:
            value: Decimal value
            
        Returns:
            Fraction string
        """
        if value == 0.0:
            return "+0"
        
        result = "-" if value < 0.0 else "+"
        abs_value = abs(value)
        
        if abs_value > 1.0:
            result += str(int(round_down(abs_value)))
            abs_value -= round_down(abs_value)
        
        if abs_value == 0.0:
            return result
        
        best_match = 1.0
        fraction_str = ""
        
        if abs(0.25 - abs_value) < best_match:
            best_match = abs(0.25 - abs_value)
            fraction_str = "1/4"
        if abs(0.5 - abs_value) < best_match:
            best_match = abs(0.5 - abs_value)
            fraction_str = "1/2"
        if abs(0.75 - abs_value) < best_match:
            best_match = abs(0.75 - abs_value)
            fraction_str = "3/4"
        if abs(1.0 - abs_value) < best_match:
            fraction_str = ""
            if len(result) > 1:
                num = int(result[1:])
                result = result[0] + str(num + 1)
            else:
                result += "1"
        
        if len(result) > 1:
            result += " "
        result += fraction_str
        
        return result.strip()
    
    def set_custom(self, custom: bool) -> None:
        """Set custom flag."""
        self.custom = custom
        self._minimum_cost = 1.0
        self.min_set = True
        self.max_set = True
        self._max_cost = 5.0
    
    @property
    def ocv_value(self) -> int:
        """Get OCV value as integer."""
        ocv_str = self.ocv.strip()
        if ocv_str.startswith("+"):
            ocv_str = ocv_str[1:]
        try:
            return int(ocv_str)
        except (ValueError, TypeError):
            return 0
    
    @property
    def dcv_value(self) -> int:
        """Get DCV value as integer."""
        dcv_str = self.dcv.strip()
        if dcv_str.startswith("+"):
            dcv_str = dcv_str[1:]
        try:
            return int(dcv_str)
        except (ValueError, TypeError):
            return 0
    
    def _replace(self, text: str, old: str, new: str) -> str:
        """Replace string occurrences."""
        while old in text:
            idx = text.index(old)
            if idx == 0:
                text = new.strip() + " " + text[len(old):].strip()
            else:
                prefix = text[:idx]
                suffix = text[idx + len(old):]
                if new.strip():
                    text = prefix.strip() + " " + new.strip() + " " + suffix.strip()
                else:
                    text = prefix.strip() + " " + suffix.strip()
        return text.strip()
    
    def total_dc(self, primary: bool = True, limit_str: bool = False) -> float:
        """
        Get total damage classes including STR.
        
        Args:
            primary: Use primary STR value
            limit_str: Limit STR contribution
            
        Returns:
            Total DC value
        """
        base_dc = float(self.total_dc_no_str)
        dc = base_dc
        
        if self.add_str:
            active_hero = EngineContext.active_hero()
            if active_hero:
                str_char = active_hero.characteristic(1)  # STR
                if str_char:
                    if primary:
                        if str_char.get_primary_value(active_hero) > 0.0:
                            dc += str_char.get_primary_value(active_hero) / 5.0
                    else:
                        if str_char.get_secondary_value(active_hero) > 0.0:
                            dc += str_char.get_secondary_value(active_hero) / 5.0
        
        if limit_str and dc > base_dc * 2.0:
            dc = base_dc * 2.0
        
        if limit_str and self.max_str > 0:
            self.max_str = int((dc - base_dc) * 5)
        
        return dc
    
    @property
    def total_dc_no_str(self) -> int:
        """Get total damage classes without STR."""
        dc = self.dcs
        is_hth = self.category.upper() != "RANGED"
        
        active_hero = EngineContext.active_hero()
        if active_hero:
            for maneuver in active_hero.maneuvers:
                if isinstance(maneuver, ExtraDamageClasses) and is_hth:
                    dc += maneuver.levels
                elif isinstance(maneuver, RangedDamageClasses) and not is_hth:
                    dc += maneuver.levels
        
        return dc
    
    @property
    def normal_dc(self) -> str:
        """Get normal damage class string."""
        primary_dc = self.total_dc(True, False)
        secondary_dc = self.total_dc(False, False)
        
        if primary_dc < 0.5 and secondary_dc < 0.5:
            return ""
        
        result = " "
        result += str(int(round_down(primary_dc)))
        if primary_dc - round_down(primary_dc) >= 0.5:
            result += " 1/2"
        result += "d6"
        
        if primary_dc != secondary_dc:
            result += " / "
            result += str(int(round_down(secondary_dc)))
            if secondary_dc - round_down(secondary_dc) >= 0.5:
                result += " 1/2"
            result += "d6"
        
        return result
    
    @property
    def weapon_dc(self) -> str:
        """Get weapon damage class string."""
        dc = self.total_dc_no_str
        if dc == 0:
            return ""
        result = " "
        if dc > 0:
            result += "+"
        result += str(dc) + " DC "
        return result
    
    @property
    def flash_dc(self) -> str:
        """Get flash damage class string."""
        dc = self.total_dc_no_str
        if dc < 0.5:
            return ""
        result = " Flash "
        result += str(int(round_down(dc)))
        if dc - round_down(dc) >= 0.5:
            result += " 1/2"
        result += "d6"
        return result
    
    @property
    def nnd_dc(self) -> str:
        """Get NND damage class string."""
        dc = self.total_dc_no_str
        if dc < 0.5:
            return ""
        nnd_dc = dc / 2.0
        fraction = self.fraction(nnd_dc)
        if fraction.startswith("+"):
            fraction = fraction[1:]
        return " " + fraction + "d6 NND"
    
    @property
    def str_dc(self) -> str:
        """Get STR damage class string."""
        primary_dc = self.total_dc(True, False)
        secondary_dc = self.total_dc(False, False)
        
        if primary_dc < 0.5 and secondary_dc < 0.5:
            return ""
        
        result = " "
        result += f"{int(primary_dc * 5.0)} STR "
        if primary_dc != secondary_dc:
            result += f" / {int(secondary_dc * 5.0)} STR "
        return result
    
    @property
    def killing_dc(self) -> str:
        """Get killing damage class string."""
        dc = self.total_dc_no_str
        primary_dc = self.total_dc(True, True)
        secondary_dc = self.total_dc(False, True)
        
        template = EngineContext.active_template()
        is_6e = template and template.is_6e()
        
        multiplier = 1.0 if is_6e else 2.0
        
        if is_6e:
            primary_dc = self.total_dc(True, False)
            secondary_dc = self.total_dc(False, False)
        else:
            base_dc = dc / multiplier
            if primary_dc - dc >= base_dc:
                primary_dc = base_dc + base_dc
            else:
                primary_dc = base_dc + (primary_dc - dc)
            if secondary_dc - dc >= base_dc:
                secondary_dc = base_dc + base_dc
            else:
                secondary_dc = base_dc + (secondary_dc - dc)
        
        if primary_dc < 0.5 and secondary_dc < 0.5:
            return ""
        
        result = ""
        dice = int(round_down(primary_dc / 3.0))
        remainder = int(primary_dc % 3.0)
        result = str(dice)
        if remainder == 1:
            result += "d6 +1"
        elif remainder == 2:
            result += " 1/2d6"
        else:
            result += "d6"
        
        result = " HKA " + result
        if primary_dc != secondary_dc:
            dice = int(round_down(secondary_dc / 3.0))
            remainder = int(secondary_dc % 3.0)
            sec_str = str(dice)
            if remainder == 1:
                sec_str += "d6 +1"
            elif remainder == 2:
                sec_str += " 1/2d6"
            else:
                sec_str += "d6"
            result += " / HKA " + sec_str
        
        return result
    
    @property
    def weapon_killing_dc(self) -> str:
        """Get weapon killing damage class string."""
        dc = self.total_dc_no_str
        template = EngineContext.active_template()
        is_6e = template and template.is_6e()
        multiplier = 1.0 if is_6e else 2.0
        
        dc = int(round_down(dc / multiplier))
        if dc == 0:
            return ""
        return f" HKA {dc} DC "
    
    @property
    def damage_string(self) -> str:
        """Get damage string based on damage type."""
        if self.use_weapon:
            return ("Weapon " + self.weapon_dc).strip()
        
        if self.damage_type == self.NONE:
            return ""
        elif self.damage_type == self.STR:
            return self.str_dc
        elif self.damage_type == self.NORMAL:
            return self.normal_dc
        elif self.damage_type == self.KILLING:
            return self.killing_dc
        elif self.damage_type == self.NND:
            return self.nnd_dc
        elif self.damage_type == self.FLASH:
            return self.flash_dc
        
        return ""
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string for display."""
        # Build string from assigned modifiers
        if not hasattr(self, 'assigned_modifiers') or not self._assigned_modifiers:
            return ""
        
        parts = []
        for mod in self._assigned_modifiers:
            alias = getattr(mod, 'alias', '') or getattr(mod, 'display', '') or mod.xmlid
            if alias:
                parts.append(alias)
        
        if parts:
            return " (" + ", ".join(parts) + ")"
        return ""
    
    def set_ranged(self, ranged: int) -> None:
        """Set ranged value."""
        self.ranged = ranged
        self.category = "Ranged" if ranged >= 0 else "Hand To Hand"
    
    @property
    def use_weapon(self) -> bool:
        """Whether weapon is used."""
        return self._use_weapon

    @use_weapon.setter
    def use_weapon(self, value: bool) -> None:
        self._use_weapon = value
    
    def set_effect(self, effect: str) -> None:
        """Set effect."""
        self.effect = effect
        self.weapon_effect = effect
    
    @property
    def column3_output(self) -> Optional[str]:
        """Get column 3 output (END usage)."""
        if self.end_usage == 0:
            return None
        return str(self.end_usage)
    
    @property
    def maneuver_effect(self) -> str:
        """Get maneuver effect string."""
        effect_str = self.weapon_effect if self.use_weapon else self.effect
        
        if "[DAMAGE]" in effect_str:
            effect_str = effect_str.replace("[DAMAGE]", self.damage_string)
            return effect_str
        else:
            damage_str = self.damage_string
            if damage_str and damage_str.strip():
                return damage_str + ", " + effect_str
            return effect_str
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        output = self._alias
        output += f":  {self.phase} Phase, {self.ocv} OCV, {self.dcv} DCV, "
        
        if self.category.upper() == "RANGED":
            sign = "+" if self.ranged >= 0 else "-"
            output += f"Range {sign}{abs(self.ranged)}, "
        
        if self.custom:
            output += self.maneuver_effect
        elif self.use_weapon:
            output += self.weapon_effect
        else:
            output += self.effect
        
        # Add END usage note
        if self.end_usage > 0:
            active_hero = EngineContext.active_hero()
            if active_hero:
                from kirby_cost.objects.base import GenericObject
                end_reserve = GenericObject.find_object_by_id(active_hero.powers, "ENDURANCERESERVE")
                if end_reserve:
                    all_mods = self.all_assigned_modifiers
                    end_reserve_mod = GenericObject.find_object_by_id(all_mods, "ENDRESERVEOREND")
                    prefs = EngineContext.prefs()
                    if not end_reserve_mod and not prefs.use_wg:
                        if self._use_end_reserve:
                            output += " (uses END Reserve)"
                        else:
                            output += " (uses Personal END)"
        
        return output
    
    @property
    def dc(self) -> int:
        """Get damage classes."""
        return self.dcs
    
    @dc.setter
    def dc(self, dc: int) -> None:
        """Set damage classes."""
        self.dcs = dc
    
    @property
    def does_damage(self) -> bool:
        """Check if maneuver does damage."""
        return self.damage_type != self.NONE
    
    def _init(self, element) -> None:
        """Initialize from XML element."""
        self._display = "???"
        self._alias = "???"
        self._base_cost = 3.0
        self._level_cost = 0.0
        self._level_value = 0.0
        self._minimum_cost = 3.0
        self._minimum_level = 0
        self.ocv = "--"
        self.dcv = "--"
        self.phase = "1/2"
        self.effect = ""
        self.weapon_effect = ""
        self.ranged = 0
        self.category = "Hand To Hand"
        self.dcs = 0
        self._use_weapon = False
        
        super()._init(element)
        
        if not self._types:
            self._types = []
        self._types.append("ATTACK")
        
        # Parse OCV
        ocv_str = XMLUtility.get_value(element, "OCV")
        if ocv_str and ocv_str.strip():
            try:
                ocv_val = int(ocv_str)
                # Normalise to +N / -N form (HDC may already include the sign).
                # Java splits this across two paths: the unsigned-template path
                # (init) prepends "+" itself, while the pre-signed character-file
                # path (loadFromXML) copies the raw value.  The Python loader
                # funnels both through _init, so it normalises here instead.
                self.ocv = ("+" if ocv_val >= 0 else "") + str(ocv_val)
            except (ValueError, TypeError):
                # Non-numeric (e.g. "--"): store as-is
                self.ocv = ocv_str
        
        # Parse CUSTOM
        custom_str = XMLUtility.get_value(element, "CUSTOM")
        self.custom = custom_str and custom_str.strip().upper().startswith("Y")
        
        # Parse ALLOWSOTHERADDERS
        allows_str = XMLUtility.get_value(element, "ALLOWSOTHERADDERS")
        self.allows_other_adders = allows_str and allows_str.strip().upper().startswith("Y")
        
        # Parse DCV
        dcv_str = XMLUtility.get_value(element, "DCV")
        if dcv_str and dcv_str.strip():
            try:
                dcv_val = int(dcv_str)
                # Normalise to +N / -N form (HDC may already include the sign)
                self.dcv = ("+" if dcv_val >= 0 else "") + str(dcv_val)
            except (ValueError, TypeError):
                # Non-numeric (e.g. "--"): store as-is
                self.dcv = dcv_str
        
        # Parse RANGE
        range_str = XMLUtility.get_value(element, "RANGE")
        if range_str and range_str.strip():
            try:
                self.ranged = int(range_str)
            except (ValueError, TypeError):
                pass
        
        # Parse ACTIVECOST
        cost_str = XMLUtility.get_value(element, "ACTIVECOST")
        if cost_str and cost_str.strip():
            try:
                self._maneuver_active_cost = int(cost_str)
            except (ValueError, TypeError):
                pass
        
        # Parse MAXSTR
        max_str_str = XMLUtility.get_value(element, "MAXSTR")
        if max_str_str and max_str_str.strip():
            try:
                self.max_str = int(max_str_str)
            except (ValueError, TypeError):
                pass
        
        # Parse STRMULT
        strmult_str = XMLUtility.get_value(element, "STRMULT")
        if strmult_str and strmult_str.strip():
            try:
                self.str_multiplier = int(strmult_str)
            except (ValueError, TypeError):
                self.str_multiplier = 1
        else:
            self.str_multiplier = 1
        
        if self.str_multiplier < 1:
            self.str_multiplier = 1
        
        # Parse ADDSTR
        addstr_str = XMLUtility.get_value(element, "ADDSTR")
        self.add_str = addstr_str and addstr_str.strip().upper().startswith("Y")
        
        # Parse DC
        dc_str = XMLUtility.get_value(element, "DC")
        if dc_str and dc_str.strip():
            try:
                self.dcs = int(dc_str)
            except (ValueError, TypeError):
                pass
        
        # Parse CATEGORY
        cat_str = XMLUtility.get_value(element, "CATEGORY")
        if cat_str and cat_str.strip():
            self.category = cat_str
        
        # Parse PHASE
        phase_str = XMLUtility.get_value(element, "PHASE")
        if phase_str and phase_str.strip():
            self.phase = phase_str
        
        # Parse EFFECT
        effect_str = XMLUtility.get_value(element, "EFFECT")
        if effect_str and effect_str.strip():
            self.effect = effect_str
        
        # Parse WEAPONEFFECT
        weap_str = XMLUtility.get_value(element, "WEAPONEFFECT")
        if weap_str and weap_str.strip():
            self.weapon_effect = weap_str
        
        # Parse USEWEAPON
        useweap_str = XMLUtility.get_value(element, "USEWEAPON")
        self._use_weapon = useweap_str and useweap_str.strip().upper().startswith("Y")
        
        # Parse DAMAGETYPE
        dmgtype_str = XMLUtility.get_value(element, "DAMAGETYPE")
        if dmgtype_str and dmgtype_str.strip():
            try:
                self.damage_type = int(dmgtype_str)
            except (ValueError, TypeError):
                pass
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        # Restore category
        cat_str = XMLUtility.get_value(element, "CATEGORY")
        if cat_str and cat_str.strip():
            self.category = cat_str
        
        # Restore OCV
        ocv_str = XMLUtility.get_value(element, "OCV")
        if ocv_str and ocv_str.strip():
            self.ocv = ocv_str
        
        # Restore DCV
        dcv_str = XMLUtility.get_value(element, "DCV")
        if dcv_str and dcv_str.strip():
            self.dcv = dcv_str
        
        # Restore DAMAGETYPE
        dmgtype_str = XMLUtility.get_value(element, "DAMAGETYPE")
        if dmgtype_str and dmgtype_str.strip():
            try:
                self.damage_type = int(dmgtype_str)
            except (ValueError, TypeError):
                pass
        
        # Restore RANGE
        range_str = XMLUtility.get_value(element, "RANGE")
        if range_str and range_str.strip():
            try:
                self.ranged = int(range_str)
            except (ValueError, TypeError):
                pass
        
        # Restore DC
        dc_str = XMLUtility.get_value(element, "DC")
        if dc_str and dc_str.strip():
            try:
                self.dcs = int(dc_str)
            except (ValueError, TypeError):
                pass
        
        # Restore PHASE
        phase_str = XMLUtility.get_value(element, "PHASE")
        if phase_str and phase_str.strip():
            self.phase = phase_str
        
        # Restore EFFECT
        effect_str = XMLUtility.get_value(element, "EFFECT")
        if effect_str and effect_str.strip():
            self.effect = effect_str
            # Handle legacy STR [NORMALDC] format
            if "STR [NORMALDC]" in self.effect:
                idx = self.effect.index("STR [NORMALDC]")
                self.effect = self.effect[:idx] + self.effect[idx + 4:]
        
        # Restore WEAPONEFFECT
        weap_str = XMLUtility.get_value(element, "WEAPONEFFECT")
        if weap_str and weap_str.strip():
            self.weapon_effect = weap_str
        
        # Restore USEWEAPON
        useweap_str = XMLUtility.get_value(element, "USEWEAPON")
        self._use_weapon = useweap_str and useweap_str.strip().upper().startswith("Y")
        
        # Restore ADDSTR
        addstr_str = XMLUtility.get_value(element, "ADDSTR")
        self.add_str = addstr_str and addstr_str.strip().upper().startswith("Y")
        
        # Restore ACTIVECOST
        cost_str = XMLUtility.get_value(element, "ACTIVECOST")
        if cost_str and cost_str.strip():
            try:
                self._maneuver_active_cost = int(cost_str)
            except (ValueError, TypeError):
                pass
        
        # Restore MAXSTR
        max_str_str = XMLUtility.get_value(element, "MAXSTR")
        if max_str_str and max_str_str.strip():
            try:
                self.max_str = int(max_str_str)
            except (ValueError, TypeError):
                pass
        
        # Restore STRMULT
        strmult_str = XMLUtility.get_value(element, "STRMULT")
        if strmult_str and strmult_str.strip():
            try:
                self.str_multiplier = int(strmult_str)
            except (ValueError, TypeError):
                self.str_multiplier = 1
        
        # Restore CUSTOM
        custom_str = XMLUtility.get_value(element, "CUSTOM")
        self.custom = custom_str and custom_str.strip().upper().startswith("Y")
    
    def get_save_xml(self):
        """Get XML element for saving."""
        element = super().get_save_xml()
        element.tag = "MANEUVER"
        
        if self.custom:
            element.set("CUSTOM", "Yes")
        element.set("CATEGORY", self.category)
        element.set("DISPLAY", str(self._display))
        element.set("OCV", str(self.ocv))
        element.set("DCV", str(self.dcv))
        element.set("DC", str(self.dc))
        element.set("PHASE", self.phase)
        element.set("EFFECT", self.effect)
        element.set("ADDSTR", "Yes" if self.add_str else "No")
        element.set("ACTIVECOST", str(self._maneuver_active_cost))
        element.set("DAMAGETYPE", str(self.damage_type))
        element.set("MAXSTR", str(self.max_str))
        element.set("STRMULT", str(self.str_multiplier))
        element.set("USEWEAPON", "Yes" if self._use_weapon else "No")
        
        if self.weapon_effect and self.weapon_effect.strip():
            element.set("WEAPONEFFECT", self.weapon_effect)
        
        if self.category.upper() == "RANGED":
            element.set("RANGE", str(self.ranged))
        
        return element
    
