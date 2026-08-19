"""
Skill class for kirby-cost.

Converted from com.hero.objects.skills.Skill.java

This is the base class for all skills in Hero Designer.
"""

from typing import Optional, List, TYPE_CHECKING
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.skills.characteristic_choice import CharacteristicChoice
from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.powers.automaton import Automaton
from kirby_cost.util.constants import CharacteristicType, characteristic_integer, characteristic_string
from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.util.rounder import round_half_down, round_half_up

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.objects.adder import Adder
    from kirby_cost.objects.modifier import Modifier


class Skill(GenericObject):
    """
    Base class for all skills in Hero Designer.

    Subclasses that are not roll-based should set:
        ``_roll_based_default: ClassVar[bool] = False``

    Skills can be:
    - Roll-based (most skills)
    - Level-only (combat levels, skill levels)
    - Familiarity (1 point for 8-)
    - Proficiency (2 points for 10-)
    - Everyman (free familiarity)
    
    Handles:
    - Characteristic-based roll calculations
    - Familiarity and proficiency handling
    - Level-only mode
    - Roll value calculations
    - Display formatting
    - Cost calculations with skill maxima
    """

    def to_build_dict(self) -> dict:
        d = super().to_build_dict()
        # Marker: the rebuild re-emits a SKILL element tag, so a skill bought
        # in the POWERS section still dispatches through the skill registry.
        d["skill"] = True
        d["familiarity"] = bool(self.is_familiarity)
        d["proficiency"] = bool(self.is_proficiency)
        d["levels_only"] = bool(self.levels_only)
        d["everyman"] = bool(self.is_everyman)
        characteristic = getattr(self, "characteristic_string", "")
        if characteristic:
            d["characteristic"] = characteristic
        return d


    #: The characteristic a skill rolls against. Stored as a CharacteristicType
    #: int, written as a name, and never read at all until now: every skill
    #: re-exported as GENERAL, which costs 2 where INT costs 3.
    XML_ATTRS = (
        #: Read by BOTH the table and set_characteristic(), deliberately.
        #: Gating the table off (read=False) and leaving it to the richer path
        #: broke the round trip: the two are not equivalent, and the table's
        #: plain assignment is doing work set_characteristic does not.
        XMLAttr("CHARACTERISTIC", "characteristic",
                parse_with=characteristic_integer,
                format_with=characteristic_string),
    )

    
    def __init__(self, xmlid: str = "SKILL"):
        """Initialize a Skill."""
        super().__init__()
        self.xmlid = xmlid
        
        # Characteristic
        self.characteristic: int = 0
        self.characteristic_choices: List[CharacteristicChoice] = []
        
        # Familiarity and proficiency
        self.familiarity: bool = False
        self.proficiency: bool = False
        self.everyman: bool = False
        self.familiarity_cost: int = 1
        self.familiarity_roll: int = 8
        self.proficiency_cost: int = 2
        self.proficiency_roll: int = 10
        self._include_familiarity: bool = False
        self._include_proficiency: bool = False
        
        # Level-only mode
        self._levels_only: bool = False
        self.display_levels_only: bool = False
        
        # Type flags
        self.scientist: bool = False
        self.professional: bool = False
        self.language: bool = False
        self.knowledge: bool = False
        self.area: bool = False
        self.contact: bool = False
        
        # Display
        self.roll_based: bool = getattr(self.__class__, '_roll_based_default', True)
        self.show_roll: bool = True
        
        # Default values
        self._duration = "CONSTANT"
        self.target = "SELFONLY"
        if "SPECIAL" not in self._types:
            self._types.append("SPECIAL")

        # 6E Skill class defaults (Java Skill.init())
        # level_cost/level_value are class defaults; BASECOST comes from HDC XML.
        # For non-standard skills (WF, TF, CombatLevels), the template JSON
        # or HDC OPTIONID will override these via _apply_template_defaults().
        if xmlid not in ("GENERIC_OBJECT", "LIST"):
            self._level_cost = 2.0
            self._level_value = 1.0
            self._minimum_cost = 1.0
            self.min_set = True
    
    def set_characteristic(self, characteristic: int) -> None:
        """Set the characteristic type."""
        for choice in self.characteristic_choices:
            if choice.characteristic != characteristic:
                continue
            self.characteristic = characteristic
            if choice.base_cost >= 0.0:
                self.base_cost = choice.base_cost
            if choice.level_cost >= 0.0:
                self.set_level_cost(choice.level_cost)
            if choice.level_value >= 0.0:
                self.set_level_value(choice.level_value)
            if choice.min_set:
                self.set_minimum_cost(choice.minimum_cost)
            if choice.minimum_level >= 0:
                self._minimum_level = choice.minimum_level
    
    @property
    def characteristic_string(self) -> str:
        """Get the characteristic name string."""
        if self.characteristic < 0:
            return ""
        return characteristic_string(self.characteristic)
    
    @property
    def is_familiarity(self) -> bool:
        """Check if this is a familiarity."""
        return self.familiarity and not self.proficiency

    @property
    def is_proficiency(self) -> bool:
        """Check if this is a proficiency."""
        return self.proficiency

    @property
    def is_everyman(self) -> bool:
        """Check if this is an everyman skill."""
        if not self.is_familiarity:
            return False
        return self.everyman
    
    def set_familiarity(self, value: bool) -> None:
        """Set familiarity flag."""
        if value:
            self._levels_only = False
        self.familiarity = value
    
    def set_proficiency(self, value: bool) -> None:
        """Set proficiency flag."""
        if value:
            self._levels_only = False
        self.proficiency = value
    
    def set_everyman(self, value: bool) -> None:
        """Set everyman flag."""
        if value:
            self._levels_only = False
        self.everyman = value
    
    def include_familiarity(self) -> bool:
        """Check if familiarity is included."""
        return self._include_familiarity
    
    def include_proficiency(self) -> bool:
        """Check if proficiency is included."""
        return self._include_proficiency
    
    @property
    def levels_only(self) -> bool:
        """Check if this is level-only mode."""
        if (self.roll.strip() and 
            self._level_cost > 0.0 and 
            self._level_value != 0.0):
            return self._levels_only
        return False
    
    def levels_only_allowed(self) -> bool:
        """Check if level-only mode is allowed."""
        return (self.roll.strip() and 
                self._level_cost > 0.0 and 
                self._level_value != 0.0)
    
    @levels_only.setter
    def levels_only(self, value: bool) -> None:
        """Set level-only mode."""
        if value:
            self.familiarity = False
            self.everyman = False
            self.proficiency = False
        self._levels_only = (self.roll.strip() and 
                            self._level_cost > 0.0 and 
                            self._level_value != 0.0) and value
    
    @property
    def base_cost(self) -> float:
        """Get base cost (overrides base class)."""
        if self.is_familiarity and self.is_everyman:
            return 0.0
        if self.is_familiarity and float(self.familiarity_cost) < super().base_cost:
            return float(self.familiarity_cost)
        if self.is_proficiency and float(self.proficiency_cost) < super().base_cost:
            return float(self.proficiency_cost)
        if self.levels_only:
            return 0.0
        return super().base_cost

    @base_cost.setter
    def base_cost(self, value) -> None:
        self._base_cost = value
    
    @property
    def minimum_cost(self) -> float:
        """Get minimum cost (overrides base class)."""
        if self.is_everyman:
            return 0.0
        if self.is_familiarity:
            return float(self.familiarity_cost)
        if self.is_proficiency:
            return float(self.proficiency_cost)
        if self.levels_only:
            return 0.0
        return self._minimum_cost

    @minimum_cost.setter
    def minimum_cost(self, value) -> None:
        self._minimum_cost = value
    
    @property
    def levels(self) -> int:
        """Get levels (overrides base class)."""
        if self.is_familiarity:
            return 0
        if self.is_proficiency:
            return 0
        return self._levels

    @levels.setter
    def levels(self, value) -> None:
        self._levels = value
    
    @property
    def real_cost_pre_list(self) -> float:
        """Get real cost before list adjustments (overrides base class)."""
        # Check for custom adders
        has_custom_adder = False
        for adder in self.assigned_adders:
            if GenericObject.find_object_by_id(self.available_adders, adder.xmlid) is None:
                has_custom_adder = True
                break
        
        if has_custom_adder:
            return super().real_cost_pre_list
        
        if self.is_familiarity and self.is_everyman:
            return 0.0
        
        return super().real_cost_pre_list
    
    @property
    def total_cost(self) -> float:
        """Get total cost (overrides base class)."""
        d = self.base_cost
        available_adders = self.available_adders
        
        if self._level_value != 0.0:
            d += float(self._levels) / self._level_value * self._level_cost
            
            # Skill maxima handling
            if (self._levels > 0 and 
                self._get_active_hero() is not None and
                self._get_active_hero().rules.use_skill_maxima and 
                self.roll_based):
                maxima_limit = self._get_active_hero().rules.skill_maxima_limit
                roll_value = self.roll_value
                secondary_roll = self.secondary_roll_value
                if secondary_roll > roll_value:
                    roll_value = secondary_roll
                if roll_value > maxima_limit:
                    excess = roll_value - maxima_limit
                    if excess > self._levels:
                        excess = self._levels
                    d += float(excess) / self._level_value * self._level_cost
            
            # Rounding for skills with level cost < level value
            if self._level_cost < self._level_value:
                d = 1.0 if (d > 0.0 and d < 1.0) else round_half_down(d)
        
        # Add required adders
        for adder in self.assigned_adders:
            if adder.is_required:
                d += adder.real_cost
        
        # Add available adders
        for adder in self.assigned_adders:
            if (not adder.is_required and 
                GenericObject.find_object_by_id(available_adders, adder.xmlid) is not None):
                d += adder.real_cost
        
        # Apply min/max limits
        if d < self.minimum_cost and self.min_set and not self.levels_only:
            d = self.minimum_cost
        elif d > self._max_cost and self.max_set and not self.levels_only:
            d = self._max_cost
        
        # Add custom adders
        for adder in self.assigned_adders:
            if (not adder.is_required and 
                GenericObject.find_object_by_id(available_adders, adder.xmlid) is None):
                d += adder.real_cost
        
        # Automaton defense skill multiplier
        if ("DEFENSE" in self.types and 
            self._get_active_hero() is not None):
            automaton = GenericObject.find_object_by_id(
                self._get_active_hero().powers, "AUTOMATON")
            if (automaton is not None and 
                isinstance(automaton, Automaton) and
                automaton.selected_option is not None and
                automaton.selected_option.xmlid.upper().startswith("NOSTUN")):
                d *= float(automaton.defense_cost_multiplier)
        
        return d
    
    def _get_active_hero(self) -> Optional['Hero']:
        """The character this skill belongs to.

        Java reads ``HeroDesigner.getActiveHero()`` in six places here, and
        every one of them decides a ROLL: a characteristic-based skill is
        ``9 + (CHAR/5)``, so without the character there is no roll to state.

        This returned None unconditionally until 2026-08-19, and the comment
        where the lookup belonged said so. Nothing failed, because the caller
        has a no-hero fallback that assumes a characteristic of 10 — and
        ``Rules.general_level`` is also 10, so the fallback agreed with itself
        and produced a plausible 11- for every PRE, DEX or INT skill in the
        corpus. Costs never noticed: they do not read the roll.
        """
        if getattr(self, '_hero', None) is not None:
            return self._hero
        try:
            from kirby_cost.core.context import EngineContext
            return EngineContext.active_hero()
        except Exception:  # noqa: BLE001
            return None
    
    def _is_focus(self) -> bool:
        """Check if this skill has FOCUS modifier."""
        if GenericObject.find_object_by_id(self.assigned_modifiers, "FOCUS") is not None:
            return True
        parent = self._parent
        if parent is not None:
            return GenericObject.find_object_by_id(parent.assigned_modifiers, "FOCUS") is not None
        return False
    
    @property
    def roll_value(self) -> int:
        """Get the roll value (primary)."""
        n = 0
        
        if self.is_familiarity:
            n = self.familiarity_roll if self.familiarity_roll > 0 else 8
        elif self.is_proficiency:
            n = self.proficiency_roll if self.proficiency_roll > 0 else 10
        elif self._is_focus() and self._get_active_hero() is not None:
            n = self._get_active_hero().rules.skill_roll_base
            if self._levels < 0:
                n = self._minimum_level
            else:
                n += self._levels
        elif self._get_active_hero() is not None:
            char = self._get_active_hero().characteristic(self.characteristic)
            rules = self._get_active_hero().rules
            n = rules.skill_roll_base
            
            if char is not None and char.xmlid != "GENERAL":
                n = (rules.skill_roll_base + 
                     int(round_half_up(char.get_primary_value(self._get_active_hero()) / rules.skill_roll_denominator) + 
                         float(self._levels) * self._level_value))
            elif self.characteristic == 0:
                n = (rules.skill_roll_base + 
                     int(round_half_up(float(rules.general_level) / rules.skill_roll_denominator) + 
                         float(self._levels) * self._level_value))
            else:
                n = (rules.skill_roll_base + 
                     int(round_half_up(float(self._levels) * self._level_value)))
        else:
            # Fallback when no active hero
            n = (9 + int(round_half_up(float(10) / 5.0) + 
                         float(self._levels) * self._level_value))
        
        return n
    
    @property
    def secondary_roll_value(self) -> int:
        """Get the secondary roll value."""
        n = 0
        
        if self.is_familiarity:
            n = self.familiarity_roll if self.familiarity_roll > 0 else 8
        elif self.is_proficiency:
            n = self.proficiency_roll if self.proficiency_roll > 0 else 10
        elif self._is_focus() and self._get_active_hero() is not None:
            n = self._get_active_hero().rules.skill_roll_base
            if self._levels < 0:
                n = self._minimum_level
            else:
                n += self._levels
        elif self._get_active_hero() is not None:
            char = self._get_active_hero().characteristic(self.characteristic)
            rules = self._get_active_hero().rules
            n3 = rules.skill_roll_base
            n4 = rules.skill_roll_base
            
            if char is not None and char.xmlid != "GENERAL":
                n3 = (rules.skill_roll_base + 
                      int(round_half_up(char.get_primary_value(self._get_active_hero()) / rules.skill_roll_denominator) + 
                          float(self._levels) * self._level_value))
                n4 = (rules.skill_roll_base + 
                      int(round_half_up(char.get_secondary_value(self._get_active_hero()) / rules.skill_roll_denominator) + 
                          float(self._levels) * self._level_value))
            elif self.characteristic == 0:
                n3 = n4 = (rules.skill_roll_base + 
                           int(round_half_up(float(rules.general_level) / rules.skill_roll_denominator) + 
                               float(self._levels) * self._level_value))
            else:
                n3 = (rules.skill_roll_base + 
                      int(round_half_up(float(self._levels) * self._level_value)))
                n4 = n3
            n = n4
        else:
            # Fallback when no active hero
            n = (9 + int(round_half_up(float(10) / 5.0) + 
                         float(self._levels) * self._level_value))
        
        return n
    
    @property
    def roll(self) -> str:
        """Get the roll string for display."""
        if self.display_levels_only:
            return ""
        if self._levels_only:
            sign = "+" if self._levels >= 0 else "-"
            return f"{sign}{self._levels} with {self._alias}"
        if self._level_value < 1.0 and self._level_cost < 1.0:
            return ""
        
        n = self.roll_value
        n2 = self.secondary_roll_value
        
        if n == 0:
            return ""
        
        if n != n2:
            return f"{n}- ({n2}-)"
        return f"{n}-"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output for display."""
        if self.levels_only:
            return self._get_level_only_output()
        
        string2 = self._alias
        if self.display_levels_only:
            string2 = "+" if self._levels > 0 else ""
            string2 = f"{string2}{self._levels}"
        
        if self._name and self._name.strip():
            string2 = f"<i>{self._name}:</i>  {string2}"
        
        if self.input and self.input.strip():
            string2 = f"{string2}:  {self.input}"
        
        if self._selected_option is not None:
            if not self.display_levels_only:
                string2 = f"{string2}:  {self._selected_option.alias}"
            else:
                string2 = f"{string2} {self._selected_option.alias}"
        
        # Characteristic-based note (if multiple choices and not using WG)
        # Note: Would need HeroDesigner.getInstance().getPrefs().useWG() check
        if (self.characteristic_choices and 
            len(self.characteristic_choices) > 1 and 
            self.characteristic != 0):
            string2 = f"{string2} ({characteristic_string(self.characteristic)}-based)"
        
        # Adder string
        adder_str = self.adder_string
        if adder_str.strip():
            string2 = f"{string2} ({adder_str})"
        
        # Roll
        if not self.display_levels_only and self.show_roll:
            string2 = f"{string2} {self.roll}"
        
        # Modifier string
        string2 = f"{string2}{self.modifier_string}"
        
        # END Reserve note
        # Note: Would need EngineContext checks
        # if (self.get_end_usage() > 0 and 
        #     GenericObject.find_object_by_id(self._get_active_hero().get_powers(), "ENDURANCERESERVE") is not None and
        #     GenericObject.find_object_by_id(self.get_all_assigned_modifiers(), "ENDRESERVEOREND") is None and
        #     not HeroDesigner.getInstance().getPrefs().useWG()):
        #     if self.use_end_reserve:
        #         string2 = f"{string2} (uses END Reserve)"
        #     else:
        #         string2 = f"{string2} (uses Personal END)"
        
        return string2
    
    @property
    def column2_output_without_roll(self) -> str:
        """Get column 2 output without roll."""
        self.show_roll = False
        old_name = self._name
        self._name = ""
        result = self.column2_output
        self.show_roll = True
        self._name = old_name
        return result
    
    @property
    def column3_output(self) -> str:
        """Get column 3 output (END usage)."""
        if self.end_usage > 0:
            return str(self.end_usage)
        return ""
    
    def _get_level_only_output(self) -> str:
        """Get level-only output string."""
        sign = "+" if self._levels >= 0 else "-"
        string2 = sign
        
        if self._name and self._name.strip():
            string2 = f"<i>{self._name}:</i>  {string2}"
        
        string2 = f"{string2}{self._levels} with {self._alias}"
        
        if self.input.strip():
            string2 = f"{string2}: {self.input}"
        
        adder_str = self.adder_string
        if adder_str.strip():
            string2 = f"{string2} ({adder_str})"
        
        string2 = f"{string2}{self.modifier_string}"
        
        # END Reserve note (stub)
        # if (self.get_end_usage() > 0 and ...):
        #     ...
        
        return string2
    
    
    
    def dialog(self, bl: bool = False, bl2: bool = False):
        """Get the skill dialog (stub)."""
        # Would return SkillDialog instance
        return None
    
    def get_save_xml(self):
        """
        Get XML element for saving this skill.
        
        Converted from com.hero.objects.skills.Skill.getSaveXML()
        
        Returns:
            lxml.etree.Element representing this skill's saved state
        """
        # Get base element from parent
        element = self.get_general_save_xml()
        
        # Set tag name to "SKILL" (not as an attribute!)
        element.tag = "SKILL"
        
        # Skill-specific attributes
        element.set("CHARACTERISTIC", characteristic_string(self.characteristic))
        element.set("FAMILIARITY", "Yes" if self.is_familiarity else "No")
        element.set("PROFICIENCY", "Yes" if self.is_proficiency else "No")
        
        if self.levels_only_allowed():
            element.set("LEVELSONLY", "Yes" if self.levels_only else "No")
        
        if self.is_familiarity:
            element.set("EVERYMAN", "Yes" if self.is_everyman else "No")
        
        return element
    
    
    def _init(self, element) -> None:
        """Initialize from XML element (stub)."""
        self.characteristic_choices = []
        self.familiarity_roll = 8
        self.proficiency_roll = 10
        self._include_familiarity = False
        self._include_proficiency = False
        self.proficiency_cost = 2
        self._duration = "CONSTANT"
        super()._init(element)
        self.target = "SELFONLY"
        if "SPECIAL" not in self._types:
            self._types.append("SPECIAL")
        
        self.scientist = "SCIENCE" in self._types
        self.professional = "PROFESSIONAL" in self._types
        self.language = "LANGUAGE" in self._types
        self.knowledge = "KNOWLEDGE" in self._types
        self.area = "AREA" in self._types
        self.contact = "CONTACT" in self._types

        # Parse CHARACTERISTIC_CHOICE children
        # Note: Would need XML parsing
        # char_choice_elem = element.find("CHARACTERISTIC_CHOICE")
        # if char_choice_elem is not None:
        #     for item_elem in char_choice_elem.findall("ITEM"):
        #         choice = CharacteristicChoice(item_elem)
        #         self.characteristic_choices.append(choice)

        # Parse FAMILIARITYROLL
        # Parse PROFICIENCYROLL
        # Parse TARGET
        # Parse FAMILIARITYCOST
        # Parse PROFICIENCYCOST
        # Parse DISPLAYLEVELSONLY

        # Parse skill-specific XML attributes
        if element is None:
            return

        char_str = element.get("CHARACTERISTIC", "")
        if char_str and char_str.strip():
            self.set_characteristic(characteristic_integer(char_str))

        fam_str = element.get("FAMILIARITY", "")
        if fam_str and fam_str.strip():
            self.set_familiarity(fam_str.upper().startswith("Y"))

        prof_str = element.get("PROFICIENCY", "")
        if prof_str and prof_str.strip():
            self.set_proficiency(prof_str.upper().startswith("Y"))

        levels_only_str = element.get("LEVELSONLY", "")
        if levels_only_str and levels_only_str.strip():
            self.levels_only = levels_only_str.upper().startswith("Y")

        everyman_str = element.get("EVERYMAN", "")
        if everyman_str and everyman_str.strip():
            self.set_everyman(everyman_str.upper().startswith("Y"))
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        char_str = element.get("CHARACTERISTIC", "")
        if char_str and char_str.strip():
            self.set_characteristic(characteristic_integer(char_str))

        fam_str = element.get("FAMILIARITY", "")
        if fam_str and fam_str.strip():
            self.set_familiarity(fam_str.upper().startswith("Y"))

        prof_str = element.get("PROFICIENCY", "")
        if prof_str and prof_str.strip():
            self.set_proficiency(prof_str.upper().startswith("Y"))
        
        levels_only_str = element.get("LEVELSONLY", "")
        if levels_only_str and levels_only_str.strip():
            self.levels_only = levels_only_str.upper().startswith("Y")
        
        everyman_str = element.get("EVERYMAN", "")
        if everyman_str and everyman_str.strip().upper().startswith("Y"):
            self.set_everyman(True)
        else:
            self.set_everyman(False)

