"""
GenericObject base class for kirby-cost.

Converted from com.hero.objects.GenericObject.java

This is the base class for all purchasable items in Hero Designer:
- Powers
- Skills
- Perks
- Talents
- Complications
- Modifiers
- Adders

All cost calculations are based on this class.
"""

import math
from typing import ClassVar, Optional, List, TYPE_CHECKING
from abc import ABC

from kirby_cost.util.rounder import round_half_down, round_half_up
from kirby_cost.io.xml_utility import XMLUtility
from kirby_cost.engine.cost import CostMixin, ENHANCER_DEFS
from kirby_cost.engine.modifiers import ModifierMixin
from kirby_cost.engine.serialize import SerializationMixin

if TYPE_CHECKING:
    from kirby_cost.objects.adder import Adder
    from kirby_cost.objects.modifier import Modifier
    from kirby_cost.objects.list import List as HeroList


class GenericObject(CostMixin, ModifierMixin, SerializationMixin, ABC):
    """
    Base class for all purchasable items in Hero Designer.
    
    Handles:
    - Base cost calculations
    - Active cost calculations (with advantages)
    - Real cost calculations (with limitations)
    - END cost calculations
    - Level-based cost calculations
    - Adder and modifier management
    """
    
    # Static ID counter
    _id_count = 0
    
    # ── Class registry ────────────────────────────────────────
    _registry: ClassVar[dict[str, type['GenericObject']]] = {}

    def __init_subclass__(cls, xmlid: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if xmlid:
            cls._registry[xmlid] = cls
            cls.XMLID = xmlid

    # ID translations for backward compatibility
    _id_translations = {
        "RADIOTRANSMISSION": "RADIOPERCEIVETRANSMIT",
        "IRPERCEPTION": "INFRAREDPERCEPTION",
        "NRAY": "NRAYPERCEPTION",
        "UVPERCEPTION": "ULTRAVIOLETPERCEPTION",
        "HEARING": "HEARINGGROUP",
        "RADIO": "RADIOGROUP",
        "SIGHT": "SIGHTGROUP",
        "MENAL": "MENTALGROUP",
        "SMELL": "SMELLGROUP",
        "TOUCH": "TOUCHGROUP",
    }
    
    def __init__(self):
        """Initialize a new GenericObject."""
        GenericObject._id_count += 1
        self._id = GenericObject._id_count
        
        # Core identification
        self.xmlid: str = "GENERIC_OBJECT"
        self._name: str = ""
        self._display: str = ""
        self._alias: str = ""
        self.abbreviation: str = ""
        self.definition: str = ""
        self.notes: str = ""
        self.comments: str = ""
        
        # Cost fields
        self._base_cost: float = 0.0
        self.orig_base_cost: float = 0.0
        self._base_cost_from_xml: bool = False
        self._level_value_from_xml: bool = False
        self._level_cost: float = 0.0
        self._level_value: float = 0.0
        self._levels: int = 0
        self.level_power: int = 0
        self.level_multiplier: int = 1
        self._minimum_cost: float = 0.0
        self._max_cost: float = 0.0
        self.min_set: bool = False
        self.max_set: bool = False
        self.multiplier: float = 1.0
        self._minimum_level: int = 0
        self._max_level: int = 999999
        
        # Modifiers and adders
        self._assigned_modifiers: List['Modifier'] = []
        self._available_modifiers: List['Modifier'] = []
        self._assigned_adders: List['Adder'] = []
        self._available_adders: List['Adder'] = []
        self._options: List['Adder'] = []
        self._selected_option: Optional['Adder'] = None
        
        # Type and category
        self._types: List[str] = []
        self._is_power: bool = False  # Use underscore - accessed via is_power() method
        self._is_equipment: bool = False
        self.exclusive: bool = True
        
        # Display and behavior
        self.visible: bool = False
        self.uses_end: bool = False
        self._does_damage: bool = False  # Use underscore to avoid conflict with method
        self.does_body: bool = False
        self.killing: bool = False
        self.does_knockback: bool = False
        self.display_active_cost: bool = False
        
        # Range, target, duration
        self.range: str = ""
        self.target: str = "N/A"
        self._duration: str = ""
        self._defense: str = "NONE"
        
        # Parent relationship
        self._parent: Optional['HeroList'] = None
        self.parent_id: int = 0
        self.main_power: Optional['GenericObject'] = None
        
        # Other fields
        self.position: int = 0
        self.position_locked: bool = False
        self._quantity: int = 1
        self.price: float = 0.0
        self._weight: float = 0.0
        self.carried: bool = True
        self.ultra: bool = True
        self.fixed_value: bool = True
        self.allows_other_adders: bool = True
        self.allows_other_modifiers: bool = True
        self._included_in_template: bool = True
        self.include_notes_in_printout: bool = False
        self.show_build_dialog: bool = True
        self.show_option: bool = True
        self.stop_sign: bool = False
        self.warn_sign: bool = False
        self.dynamic_display: bool = False
        self.user_input: bool = False
        self.other_input_allowed: bool = False
        self.input: str = ""
        self.input_label: str = ""
        self.graphic: str = ""
        self.color: str = ""
        self.sfx: str = ""
        self.levels_lbl: str = ""
        self.option_lbl: str = ""
        self.text_output: str = ""
        
        # END cost related
        self.costs_end_to_maintain: bool = True
        self._continuing_effect: bool = False
        self._use_end_reserve: bool = False
        
        # Sources
        self._sources: List[str] = []
        
        # Enhancer
        self.enhancer_applied: Optional['Enhancer'] = None
        
        # List modifier check flag
        self.list_mod_check: bool = False

    # ── Template application ─────────────────────────────────────

    def apply_template(self, tmpl: "TemplateData", option_id: str = None) -> None:
        """Apply template defaults to this object's cost attributes.

        *option_id* selects a specific option within the template (resolved
        via ``option_aliases`` first).  Option values take precedence over
        base template values; XML-supplied values (``_base_cost_from_xml``)
        take precedence over both.
        """
        from kirby_cost.template.dataclasses import OptionTemplate  # noqa: F811

        option_set_lc = False
        option_set_lv = False
        option_set_lm = False

        # Resolve aliases
        if option_id and tmpl.option_aliases:
            if option_id not in tmpl.options:
                for pattern, target in tmpl.option_aliases.items():
                    if pattern == option_id:
                        option_id = target
                        break
                    if pattern.startswith("*") and option_id.endswith(pattern[1:]):
                        option_id = target
                        break
                else:
                    option_id = tmpl.option_aliases.get("*", option_id)

        # Option-specific overrides (most authoritative after XML).
        # Options always win over the base template, even when their value
        # matches the default (e.g. level_multiplier=1 overrides a base of 2).
        if option_id:
            opt = tmpl.options.get(option_id)
            if opt:
                if opt.level_cost != 0:
                    self._level_cost = opt.level_cost
                    option_set_lc = True
                if opt.level_value != 0:
                    self._level_value = opt.level_value
                    option_set_lv = True
                self.level_power = opt.level_power
                self.level_multiplier = opt.level_multiplier
                option_set_lm = True
                if opt.base_cost != 0 and self.orig_base_cost == 0:
                    self._base_cost = opt.base_cost

        # Base template values — only when option didn't set them
        if not option_set_lc:
            if tmpl.level_cost != 0:
                self._level_cost = tmpl.level_cost
            elif tmpl.level_cost == 0 and tmpl.level_value in (0, -1, -1.0):
                self._level_cost = 0.0
                self._level_value = 0.0
        # The template wins when it states a level value, exactly as it does
        # for level_cost above. This used to apply only when the object's own
        # value was still 0.0, which silently let a class default beat the
        # template: PD initialises to 1.0, so Vehicle6E's LVLVAL="2" never took
        # and a vehicle's 13 PD cost 13 x 3 = 39 instead of 13/2 x 3 = 19.5.
        #
        # It was invisible while every character was costed against Main6E,
        # whose PD is LVLVAL="1" — the same as the class default. It surfaced
        # the moment characters began resolving their own templates. In Java
        # there is no merge to get wrong: the object IS the template's clone,
        # so the template's value is simply the object's.
        if (tmpl.level_value not in (0, -1, -1.0)
                and not option_set_lv
                and not self._level_value_from_xml):
            self._level_value = tmpl.level_value
        if self.level_power == 0 and tmpl.level_power not in (0, 1):
            self.level_power = tmpl.level_power
        if not option_set_lm and self.level_multiplier == 1 and tmpl.level_multiplier != 1:
            self.level_multiplier = tmpl.level_multiplier

        # Min/max — template is authoritative
        if tmpl.min_set:
            self._minimum_cost = tmpl.minimum_cost
            self.min_set = True
        else:
            self.min_set = False
            self._minimum_cost = 0.0
        if tmpl.max_set:
            self._max_cost = tmpl.max_cost
            self.max_set = True
        else:
            self.max_set = False

        # Sense rates — the template is the only source. A sense adder charges
        # all_cost / group_cost / sense_cost depending on what it was bought
        # for (see SenseAdder.selected_option), and only the element knows the
        # three numbers.
        for _rate in ("all_cost", "group_cost", "sense_cost"):
            _value = getattr(tmpl, _rate, -1.0)
            if _value != -1.0 and hasattr(self, _rate):
                setattr(self, _rate, _value)

        # Duration, target, uses_end
        if tmpl.uses_end:
            self.uses_end = True
        if tmpl.duration and not self._duration:
            self._duration = tmpl.duration
        if tmpl.target and self.target in ("", "N/A"):
            self.target = tmpl.target

    # ── Polymorphic methods (overridden in subclasses) ──────────
    # These remain as methods because subclasses override them.

    @property
    def base_cost(self) -> float:
        """Get the base cost. Override in subclasses for computed costs."""
        return self._base_cost

    @base_cost.setter
    def base_cost(self, cost: float) -> None:
        """Set the base cost, tracking original if first assignment."""
        self._base_cost = cost
        if self.orig_base_cost == 0.0:
            self.orig_base_cost = cost

    @property
    def levels(self) -> int:
        """Get the number of levels. Override in subclasses."""
        return self._levels

    @levels.setter
    def levels(self, value: int) -> None:
        self._levels = value

    @property
    def level_cost(self) -> float:
        """Get the cost per level. Override in subclasses."""
        return self._level_cost

    @level_cost.setter
    def level_cost(self, value: float) -> None:
        self._level_cost = value

    @property
    def level_value(self) -> float:
        """Get the value per level. Override in subclasses."""
        return self._level_value

    @level_value.setter
    def level_value(self, value: float) -> None:
        self._level_value = value

    @property
    def minimum_level(self) -> int:
        """Get the minimum level. Override in subclasses."""
        return self._minimum_level

    @minimum_level.setter
    def minimum_level(self, value: int) -> None:
        self._minimum_level = value

    @property
    def minimum_cost(self) -> float:
        """Get the minimum cost. Override in subclasses."""
        return self._minimum_cost

    @minimum_cost.setter
    def minimum_cost(self, value: float) -> None:
        self._minimum_cost = value

    @property
    def max_cost(self) -> float:
        """Get the maximum cost. Override in subclasses."""
        return self._max_cost

    @max_cost.setter
    def max_cost(self, value: float) -> None:
        self._max_cost = value

    # --- Auto-generated properties for renamed attributes ---

    @property
    def alias(self) -> str:
        """Get the alias."""
        return self._alias

    @alias.setter
    def alias(self, value: str) -> None:
        self._alias = value

    @property
    def name(self) -> str:
        """Get the name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def display(self) -> str:
        """Get the display string."""
        return self._display

    @display.setter
    def display(self, value: str) -> None:
        self._display = value

    @property
    def duration(self) -> str:
        """Get the duration."""
        return self._duration

    @duration.setter
    def duration(self, value: str) -> None:
        self._duration = value

    @property
    def defense(self) -> str:
        """Get the defense type."""
        return self._defense

    @defense.setter
    def defense(self, value: str) -> None:
        self._defense = value

    @property
    def available_modifiers(self) -> List['Modifier']:
        """Get the available modifiers."""
        return self._available_modifiers

    @available_modifiers.setter
    def available_modifiers(self, value: List['Modifier']) -> None:
        self._available_modifiers = value

    @property
    def parent(self) -> Optional['HeroList']:
        """Get the parent."""
        return self._parent

    @parent.setter
    def parent(self, value: Optional['HeroList']) -> None:
        self._parent = value

    @property
    def quantity(self) -> int:
        """Get the quantity."""
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        self._quantity = value

    @property
    def weight(self) -> float:
        """Get the weight."""
        return self._weight

    @weight.setter
    def weight(self, value: float) -> None:
        self._weight = value

    @property
    def max_level(self) -> int:
        """Get the maximum level."""
        return self._max_level

    @max_level.setter
    def max_level(self, value: int) -> None:
        self._max_level = value

    @property
    def sources(self) -> List[str]:
        """Get the sources."""
        return self._sources

    @property
    def use_end_reserve(self) -> bool:
        """Get whether END reserve is used."""
        return self._use_end_reserve

    @property
    def equipment(self) -> bool:
        """Get whether this is equipment."""
        return self._is_equipment

    @equipment.setter
    def equipment(self, value: bool) -> None:
        self._is_equipment = value

    @property
    def included_in_template(self) -> bool:
        """Get whether included in template."""
        return self._included_in_template

    @property
    def id(self) -> int:
        """The object's identity — assigned once, never reassigned.

        Consumers index on this: it is the only thing about an object that is
        genuinely its own. The xmlid is a TYPE ("this is an Energy Blast") and
        the name is a display string, and a character may legitimately carry
        several powers agreeing on both — so any key built from them collides,
        silently.

        Set at construction (from the source's `ID` when it supplies one,
        otherwise from the process counter) and read-only thereafter. An
        identity a caller can overwrite is not an identity: a stale handle
        would quietly start resolving to a different object instead of
        failing loudly.
        """
        return self._id

    @property
    def base_cost_from_xml(self) -> bool:
        """Get whether base cost was from XML."""
        return self._base_cost_from_xml

    @property
    def range_value(self) -> int:
        """
        Get the range value.
        Returns -1 for Line of Sight, 0 for no range, or positive for range in meters.
        """
        if self.range == "LOS" or self.range == "LINE_OF_SIGHT":
            return -1
        elif self.range == "" or self.range == "N/A":
            return 0
        else:
            try:
                return int(float(self.range))
            except (ValueError, TypeError):
                return 0
    
    @property
    def end_usage(self) -> int:
        """Get the END usage (cost per use)."""
        if hasattr(self, 'end'):
            return int(self.end)
        return 0
    
    @property
    def continuing_effect(self) -> bool:
        """Check if this power has a continuing effect."""
        if self._continuing_effect:
            return True
        # Check for Continuous, Persistent, or Inherent modifiers
        if self.find_modifier_by_id("CONTINUOUS"):
            return True
        if self.find_modifier_by_id("PERSISTENT"):
            return True
        if self.find_modifier_by_id("INHERENT"):
            return True
        # Check duration
        duration = self._duration
        return duration in ("CONTINUOUS", "PERSISTENT", "INHERENT")

    @continuing_effect.setter
    def continuing_effect(self, value: bool) -> None:
        self._continuing_effect = value
    
    @staticmethod
    def find_object_by_id(objects: List['GenericObject'], xmlid: str) -> Optional['GenericObject']:
        """Find an object by XML ID in a list. Recursively searches Lists and CompoundPowers."""
        if not objects:
            return None
        xmlid_upper = xmlid.strip().upper()
        for obj in objects:
            if hasattr(obj, 'objects'):
                found = GenericObject.find_object_by_id(obj.objects, xmlid)
                if found:
                    return found
            if obj.xmlid == "COMPOUNDPOWER" and hasattr(obj, 'powers'):
                found = GenericObject.find_object_by_id(obj.powers, xmlid)
                if found:
                    return found
            if obj.xmlid.upper() == xmlid_upper:
                return obj
        return None

    def _java_all_assigned_modifiers(self) -> List['Modifier']:
        """Java GenericObject.getAllAssignedModifiers (GenericObject.java:1323).

        Own modifiers + the parent list's, deduped by XMLID, with NO
        filtering.  (The engine's ``all_assigned_modifiers`` property applies
        VPP/CHARGES/LINKED filters consolidated from Java call sites — this
        helper is the literal Java combine used by getTarget().)
        """
        mods = list(self.assigned_modifiers)
        parent = self.parent
        if self.main_power is not None:
            parent = self.main_power.parent
        if parent is not None:
            for mod in parent.assigned_modifiers:
                if GenericObject.find_object_by_id(mods, mod.xmlid) is None:
                    mods.append(mod)
        return mods

    def effective_target(self) -> str:
        """Java GenericObject.getTarget (GenericObject.java:2805).

        The raw ``target`` attribute adjusted for assigned modifiers
        (own + parent list): BASEDONCON/UOO -> DCV, BOECV -> ECV,
        AOE/EXPLOSION -> HEX, SELFONLY -> SELFONLY (except MentalIllusions).
        Drives e.g. the Autofire +1 surcharge for non-DCV-targeted attacks.
        """
        ret = self.target
        all_mods = self._java_all_assigned_modifiers()
        if GenericObject.find_object_by_id(all_mods, "BASEDONCON") is not None:
            ret = "DCV"
        if GenericObject.find_object_by_id(all_mods, "UOO") is not None:
            ret = "DCV"
        if GenericObject.find_object_by_id(all_mods, "BOECV") is not None:
            ret = "ECV"
        if GenericObject.find_object_by_id(all_mods, "AOE") is not None:
            ret = "HEX"
        if GenericObject.find_object_by_id(all_mods, "EXPLOSION") is not None:
            ret = "HEX"
        if GenericObject.find_object_by_id(all_mods, "SELFONLY") is not None:
            from kirby_cost.objects.powers.mental_illusions import MentalIllusions
            if not isinstance(self, MentalIllusions):
                ret = "SELFONLY"
        return ret

    def __str__(self) -> str:
        return self._display if self._display else self._name if self._name else self.xmlid

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(xmlid={self.xmlid}, id={self._id})>"

    def _init(self, element) -> None:
        """
        Initialize this object from an XML element.
        
        This is called during object construction from XML.
        Subclasses should override this to handle their specific initialization.
        
        Args:
            element: XML element (lxml.etree.Element) containing object data
        """
        if element is None:
            return

        # The object's IDENTITY, when the source supplies one. Without this the
        # id is whatever `GenericObject._id_count` happened to reach while this
        # object was being constructed — unique within a process, meaningless
        # across loads. A consumer that has to find this object again then has
        # nothing to hold but the xmlid and the name, and the xmlid is a TYPE:
        # a character may carry several powers agreeing on both, so every such
        # key collides silently.
        #
        # Read on the normal load path (it was only read in
        # `restore_from_save`, which no loader calls), so an HDC file's `ID`
        # and a build doc's `id` both survive into the loaded build.
        obj_id = XMLUtility.get_value(element, "ID")
        if obj_id:
            try:
                self._id = int(obj_id)
            except (ValueError, TypeError):
                pass

        # Parse basic attributes (apply ID translation for legacy XMLIDs)
        xmlid = XMLUtility.get_value(element, "XMLID")
        if xmlid:
            self.xmlid = GenericObject._id_translations.get(xmlid, xmlid)
        
        display = XMLUtility.get_value(element, "DISPLAY")
        if display:
            self._display = display

        alias = XMLUtility.get_value(element, "ALIAS")
        if alias:
            self._alias = alias

        name = XMLUtility.get_value(element, "NAME")
        if name:
            self._name = name

        # Ensure display always has a usable value (fallback to name)
        if not self._display and self._name:
            self._display = self._name
        
        # Parse cost attributes
        basecost = XMLUtility.get_value(element, "BASECOST")
        if basecost:
            try:
                self._base_cost = float(basecost)
                self.orig_base_cost = self._base_cost
                self._base_cost_from_xml = True
            except (ValueError, TypeError):
                pass
        
        lvlcost = XMLUtility.get_value(element, "LVLCOST")
        if lvlcost:
            try:
                self._level_cost = float(lvlcost)
            except (ValueError, TypeError):
                pass
        
        lvlval = XMLUtility.get_value(element, "LVLVAL")
        if lvlval:
            try:
                self._level_value = float(lvlval)
                # Provenance, as for BASECOST: an element that states its own
                # LVLVAL outranks the template, and apply_template must not
                # overwrite it. LIGHTNING_REFLEXES_ALL is the case that proves
                # it — the template's LVLVAL halves a cost the character file
                # has already fixed.
                self._level_value_from_xml = True
            except (ValueError, TypeError):
                pass
        
        levels = XMLUtility.get_value(element, "LEVELS")
        if levels:
            try:
                self._levels = int(levels)
            except (ValueError, TypeError):
                pass
        
        mincost = XMLUtility.get_value(element, "MINCOST")
        if mincost:
            try:
                self._minimum_cost = float(mincost)
                self.min_set = True
            except (ValueError, TypeError):
                pass
        
        maxcost = XMLUtility.get_value(element, "MAXCOST")
        if maxcost:
            try:
                self._max_cost = float(maxcost)
                self.max_set = True
            except (ValueError, TypeError):
                pass
        
        # Parse other attributes
        notes = XMLUtility.get_value(element, "NOTES")
        if notes is not None:
            self.notes = notes
        
        input_val = XMLUtility.get_value(element, "INPUT")
        if input_val is not None:
            self.input = input_val

        # Parse quantity
        quantity_str = XMLUtility.get_value(element, "QUANTITY")
        if quantity_str:
            try:
                self._quantity = int(quantity_str)
            except (ValueError, TypeError):
                pass

        # Parse types (comma-separated or multiple TYPE elements)
        type_str = XMLUtility.get_value(element, "TYPE")
        if type_str:
            self._types = [t.strip() for t in type_str.split(',') if t.strip()]
        
        # Parse TYPE child elements
        for type_elem in XMLUtility.children(element, "TYPE"):
            type_val = type_elem.text
            if type_val and type_val.strip() and type_val.strip() not in self._types:
                self._types.append(type_val.strip())
    
    def restore_from_save(self, element) -> None:
        """
        Restore this object from a saved XML element.
        
        This is called when loading a character from an HDC file.
        Similar to _init but handles saved state (including IDs, positions, etc.).
        
        Args:
            element: XML element (lxml.etree.Element) containing saved object data
        """
        if element is None:
            return
        
        # Call _init first to handle basic initialization
        self._init(element)
        
        # Restore saved state
        alias = XMLUtility.get_value(element, "ALIAS")
        if alias:
            self._alias = alias
            self.abbreviation = alias
        elif not self._alias:
            self._alias = self._display
        
        text_output = XMLUtility.get_value(element, "TEXT")
        if text_output:
            self.text_output = text_output.strip()
        
        notes = XMLUtility.get_value(element, "NOTES")
        if notes is not None:
            self.notes = notes
        
        levels = XMLUtility.get_value(element, "LEVELS")
        if levels:
            try:
                self._levels = int(levels)
            except (ValueError, TypeError):
                pass
        
        basecost = XMLUtility.get_value(element, "BASECOST")
        if basecost:
            try:
                self._base_cost = float(basecost)
            except (ValueError, TypeError):
                pass
        
        multiplier = XMLUtility.get_value(element, "MULTIPLIER")
        if multiplier:
            try:
                self.multiplier = float(multiplier)
            except (ValueError, TypeError):
                self.multiplier = 1.0
        else:
            self.multiplier = 1.0
        
        obj_id = XMLUtility.get_value(element, "ID")
        if obj_id:
            try:
                self._id = int(obj_id)
            except (ValueError, TypeError):
                pass
        
        parent_id = XMLUtility.get_value(element, "PARENTID")
        if parent_id:
            try:
                self.parent_id = int(parent_id)
            except (ValueError, TypeError):
                pass
        
        position = XMLUtility.get_value(element, "POSITION")
        if position:
            try:
                self.position = int(position)
            except (ValueError, TypeError):
                pass
        
        name = XMLUtility.get_value(element, "NAME")
        if name:
            self._name = name
        
        use_end_reserve = XMLUtility.get_value(element, "USE_END_RESERVE")
        if use_end_reserve:
            self._use_end_reserve = use_end_reserve.strip().upper().startswith("Y")
        
        # Parse adders
        for adder_elem in XMLUtility.children(element, "ADDER"):
            adder = self._create_adder_from_xml(adder_elem)
            if adder:
                adder.parent = self
                adder.restore_from_save(adder_elem)
                self._assigned_adders.append(adder)
        
        # Parse modifiers
        for mod_elem in XMLUtility.children(element, "MODIFIER"):
            modifier = self._create_modifier_from_xml(mod_elem)
            if modifier:
                modifier.parent = self
                modifier.restore_from_save(mod_elem)
                if not modifier.display:
                    modifier.display = modifier.alias if modifier.alias else ""
                self._assigned_modifiers.append(modifier)
        
        # Ensure all modifiers have parent set
        for modifier in self._assigned_modifiers:
            modifier.parent = self
        
        input_val = XMLUtility.get_value(element, "INPUT")
        if input_val is not None:
            self.input = input_val
        
        # Set abbreviation from alias
        if self._alias:
            self.abbreviation = self._alias
    
    def _create_adder_from_xml(self, element) -> Optional['Adder']:
        """
        Create an Adder instance from XML element.
        
        Args:
            element: XML element containing adder data
            
        Returns:
            Adder instance or None
        """
        from kirby_cost.objects.adder import Adder
        
        xmlid = XMLUtility.get_value(element, "XMLID")
        if not xmlid:
            return None
        
        # Try to find in available adders first
        for available_adder in self.available_adders:
            if available_adder.xmlid == xmlid:
                # Clone the adder
                adder = Adder()
                adder.xmlid = available_adder.xmlid
                adder.display = available_adder.display
                adder.alias = available_adder.alias
                adder.base_cost = available_adder.base_cost
                adder.level_cost = available_adder.level_cost
                adder.level_value = available_adder.level_value
                return adder
        
        # Create new adder from XML
        adder = Adder()
        adder._init(element)
        return adder
    
    def _create_modifier_from_xml(self, element) -> Optional['Modifier']:
        """
        Create a Modifier instance from XML element.
        
        Args:
            element: XML element containing modifier data
            
        Returns:
            Modifier instance or None
        """
        from kirby_cost.objects.modifier import Modifier
        
        xmlid = XMLUtility.get_value(element, "XMLID")
        if not xmlid:
            return None
        
        # Try to find in available modifiers first
        for available_mod in self.available_modifiers:
            if available_mod.xmlid == xmlid:
                # Clone the modifier
                modifier = Modifier()
                modifier.xmlid = available_mod.xmlid
                modifier.display = available_mod.display
                modifier.alias = available_mod.alias
                modifier.base_cost = available_mod.base_cost
                modifier.level_cost = available_mod.level_cost
                modifier.level_value = available_mod.level_value
                modifier.is_limitation = available_mod.is_limitation
                return modifier
        
        # Create new modifier from XML
        modifier = Modifier()
        modifier._init(element)
        return modifier
    
    @property
    def does_damage(self) -> bool:
        """Check if this object does damage. Can be overridden by subclasses."""
        return self._does_damage

    @does_damage.setter
    def does_damage(self, value: bool) -> None:
        """Set whether this object does damage (used by attack subclasses)."""
        self._does_damage = value

    @property
    def is_power(self) -> bool:
        """
        Check if this object is a power (not a base characteristic/skill/etc).
        
        Converted from GenericObject.isPower() in Java.
        Can be overridden by subclasses for more complex logic.
        """
        if self._is_equipment:
            return True
        if self.main_power is not None:
            return self.main_power.is_power
        return self._is_power
    
    def fraction(self, value: float) -> str:
        """
        Convert a decimal value to a fraction string.
        
        Examples:
            0.25 -> "1/4"
            0.5 -> "1/2"
            0.75 -> "3/4"
            1.0 -> "1"
            1.25 -> "1 1/4"
        """
        if value == 0.0:
            return "0"
        
        sign = ""
        if value < 0.0:
            sign = "-"
            value = abs(value)
        
        whole = int(value)
        fractional = value - whole
        
        if fractional == 0.0:
            return sign + str(whole) if whole != 0 else "0"
        
        # Common fractions
        fraction_map = {
            0.25: "1/4",
            0.5: "1/2",
            0.75: "3/4",
            0.125: "1/8",
            0.375: "3/8",
            0.625: "5/8",
            0.875: "7/8",
            0.2: "1/5",
            0.4: "2/5",
            0.6: "3/5",
            0.8: "4/5",
            0.333: "1/3",
            0.667: "2/3",
        }
        
        # Find closest match
        closest_frac = None
        min_diff = float('inf')
        for frac_val, frac_str in fraction_map.items():
            diff = abs(fractional - frac_val)
            if diff < min_diff:
                min_diff = diff
                closest_frac = frac_str
        
        # If close enough, use it
        if min_diff < 0.01:
            if whole > 0:
                return sign + f"{whole} {closest_frac}"
            return sign + closest_frac
        
        # Otherwise, return decimal
        if whole > 0:
            return sign + f"{whole}.{int(fractional * 100)}"
        return sign + f"{fractional:.2f}"
    
    @property
    def column2_output(self) -> str:
        """
        Get the column 2 output string for display.
        
        This is the default implementation. Subclasses should override
        for custom formatting.
        """
        result = self._alias
        if self.input and self.input.strip():
            result = result + ": " + self.input
        if self.comments and self.comments.strip():
            result = result + " (" + self.comments + ")"
        return result
    

