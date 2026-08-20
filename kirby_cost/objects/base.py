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

from kirby_cost.util.rounder import round_half_down, round_half_up, round_up
from kirby_cost.io.xml_utility import XMLUtility
from kirby_cost.engine.cost import CostMixin, ENHANCER_DEFS
from kirby_cost.engine.modifiers import ModifierMixin
from kirby_cost.engine.serialize import SerializationMixin
from kirby_cost.engine.deserialize import DeserializationMixin
from kirby_cost.engine.xml_attrs import XMLAttr, XMLAttrsMixin, XMLField

if TYPE_CHECKING:
    from kirby_cost.objects.adder import Adder
    from kirby_cost.objects.modifier import Modifier
    from kirby_cost.objects.list import List as HeroList


class GenericObject(CostMixin, ModifierMixin, XMLAttrsMixin,
                    DeserializationMixin, SerializationMixin, ABC):
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

    #: Every attribute an HDC element carries, declared once. The loader reads
    #: these and the serializer writes them, so the two cannot drift apart.
    #: Cost-bearing attributes with side effects (MINCOST sets min_set,
    #: BASECOST records whether the XML supplied it) keep their bespoke read in
    #: _init and are declared read=False — the inventory stays single even
    #: where the reader is not.
    #: Declared AS the fields that hold them. The XML name stays explicit —
    #: nothing derives POSITION from `position` or SHOW_ACTIVE_COST from
    #: `display_active_cost`, because no rule connects them.
    position = XMLField("POSITION", "int", default=0)
    multiplier = XMLField("MULTIPLIER", "float", default=1.0)
    graphic = XMLField("GRAPHIC", default="")
    color = XMLField("COLOR", default="")
    sfx = XMLField("SFX", default="")
    display_active_cost = XMLField("SHOW_ACTIVE_COST", "yesno", default=False)
    include_notes_in_printout = XMLField("INCLUDE_NOTES_IN_PRINTOUT", "yesno",
                                         default=False)
    comments = XMLField("COMMENTS", default="")
    show_alias = XMLField("SHOWALIAS", "yesno", default=True)
    #: NOT `include_in_base`: Adder already has a method of that name, a cost
    #: concept hardcoded to False. Same word, different subject — which is why
    #: the XML name and the field name are declared separately.
    included_in_base = XMLField("INCLUDEINBASE", "yesno", default=False)
    private_mod = XMLField("PRIVATE", "yesno", default=False)
    source_option = XMLField("OPTION", default="", omit_if="")
    source_option_alias = XMLField("OPTION_ALIAS", default="", omit_if="")

    #: Rows remain where the storage is a private name __init__ owns.
    XML_ATTRS = (
        XMLAttr("QUANTITY", "_quantity", "int"),
        #: Modifier exposes `force_allow` as a property over this; binding the
        #: descriptor to the public name would have shadowed the property.
        XMLAttr("FORCEALLOW", "_force_allow", "yesno"),
        #: A sub-power of a CompoundPower is nested in the document and states
        #: its parent, but nothing linked it back: CompoundPower.powers holds
        #: the children while the children knew nothing of the compound, so
        #: both attributes vanished on write. Declared so the document's own
        #: values survive; the effective-parent logic in the serializer still
        #: overrides them when a real framework link exists.
        XMLAttr("PARENTID", "parent_id", "int"),
        XMLAttr("ULTRA_SLOT", "ultra", "yesno"),
        #: What a piece of equipment costs, weighs and whether it is being
        #: carried. Java reads all three unconditionally
        #: (GenericObject.java:3240) and writes them behind `isEquipment()`
        #: (:1929). Here nothing read them and the write was gated on
        #: `_is_equipment`, which the loader never sets — so the gate never
        #: opened and every equipped object came back stripped of all three.
        #: Declared instead of gated: the writer already states only what the
        #: document stated or the caller changed, which is the same answer the
        #: isEquipment gate was reaching for, without a flag to keep in sync.
        XMLAttr("PRICE", "price", "float"),
        XMLAttr("WEIGHT", "_weight", "float"),
        XMLAttr("CARRIED", "carried", "yesno"),
    )

    
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
        #: Sheet-display flags HD writes on every element. No field existed for
        #: the first two, so they were dropped on every write.
        #: HD writes PRIVATE on adders as well as modifiers; Modifier keeps
        #: its own, this gives adders somewhere to put it.
        #: OPTION/OPTION_ALIAS exactly as the document stated them. An object
        #: with a resolved `_selected_option` overwrites these on write; one
        #: without them kept nothing at all, losing the option on 29 elements.
        
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
        #: xmlids of the adders this object's template offers, in the
        #: template's own order. Set by apply_template; empty for an
        #: object with no template entry.
        self._template_adder_order: List[str] = []
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
        #: HD writes FORCEALLOW on adders as well as modifiers; Modifier
        #: exposes it as a property over this same name.
        self._force_allow: bool = False
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

        # Where the template says a modifier's option and input BELONG.
        #
        # HD reads SHOWOPTIONINPARENS / SHOWINPUTINPARENS / SHOWOPTIONONLY off
        # the element (Modifier.java:1002-1022) and they decide whether the
        # option is printed after the alias or inside the brackets. 32
        # modifiers in Main6E set the first and 3 set the second, and none of
        # them are ever stated by an HDC file — they are properties of the
        # modifier, not of the character. The fields existed here and stayed
        # False, so an AVAD printed
        # "Attack Versus Alternate Defense Very Common -> Rare Life Support
        # [appropriate Immunity]" instead of
        # "Attack Versus Alternate Defense (Life Support [...]; ...)".
        attrs = getattr(tmpl, "attributes", None) or {}
        for xml_name, field in (("SHOWOPTIONINPARENS", "show_option_in_parens"),
                                ("SHOWINPUTINPARENS", "show_input_in_parens"),
                                ("SHOWOPTIONONLY", "show_option_only")):
            if hasattr(self, field):
                stated = (attrs.get(xml_name) or "").strip().upper()
                if stated:
                    setattr(self, field, stated.startswith("Y"))

        # A sense usually may be moved to any group, and twelve in Main6E may
        # not — Nightvision belongs to Sight and nowhere else. HD prints the
        # group name only when there is a CHOICE of group
        # (`getAvailableGroups().size() > 1`), so leaving this at its default
        # of True made every such sense print a group HD does not:
        # "Nightvision (Sight Group)" for HD's "Nightvision".
        if hasattr(self, "allow_any_group"):
            stated = (attrs.get("ALLOWANYGROUP") or "").strip().upper()
            if stated.startswith("N"):
                self.allow_any_group = False

        # What the template CALLS this object, as distinct from what this
        # character calls it. Focus is the one that shows: HD compares
        # `getAlias()` against `getDisplay()` and prints the alias inside the
        # brackets only when they DIFFER — a character who renamed the
        # limitation gets both names, one who did not gets one. The display
        # was never filled in from the template, so it was "" on every
        # modifier, the two never matched, and 954 foci printed
        # "OIF (Focus; demonic weapon; -1/2)" for HD's
        # "OIF (demonic weapon; -1/2)". DISPLAY is not serialised, so this
        # reaches the display layer and nothing else.
        if not (self._display or "").strip() and getattr(tmpl, "display", ""):
            self._display = tmpl.display

        # The ORDER of the template's adders, which the display layer needs
        # and the cost layer does not. HD walks this list rather than the
        # character's own, so the clauses print in the order the template
        # defines them regardless of the order they sit in the HDC file.
        if getattr(tmpl, "adders", None):
            self._template_adder_order = list(tmpl.adders.keys())

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

                # Record the option as an object, not just its numbers. Java
                # keeps the chosen OPTION as an Adder and reads it back through
                # getSelectedOption(); the port consumed the costs here and
                # dropped the option on the floor, leaving _selected_option
                # None for every template-driven choice. Roughly twenty display
                # methods dereference it — CombatLevels.column2_output raised
                # AttributeError on a plain CSL as a result — and three cost
                # paths read it too (Language's similarity floor, Skill's
                # automaton NOSTUN check, KnowledgeSkill's UAA check).
                if self._selected_option is None:
                    from kirby_cost.objects.adder import Adder as _Adder
                    chosen = _Adder()
                    chosen.xmlid = opt.xmlid
                    chosen._display = opt.display
                    chosen._alias = opt.alias or opt.display
                    # The DOCUMENT outranks the template here. HD writes
                    # OPTION_ALIAS from the option it held and restores it back
                    # onto the option on load, so what the file says IS the
                    # option's alias — including when it says nothing:
                    # `OPTION="3" OPTIONID="3" OPTION_ALIAS=""` on a custom
                    # LIMITEDPOWER means the option is not to be named, and HD's
                    # guard (`getAlias().trim().length() > 0`) then prints
                    # "Only With Grab (-1/2)". Reading the template instead
                    # printed the severity text HD uses to DERIVE the value:
                    # "Only With Grab Power loses about a third of its
                    # effectiveness". Presence, not truthiness — an empty
                    # OPTION_ALIAS is a statement, an absent one is not.
                    if "OPTION_ALIAS" in (getattr(self, "_source_attrs", None) or ()):
                        chosen._alias = self.source_option_alias or ""
                    chosen._base_cost = opt.base_cost
                    chosen._selected = True
                    chosen._display_in_string = opt.display_in_string
                    chosen.parent = self
                    self._selected_option = chosen

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

        # Duration, target, uses_end.
        #
        # The XML wins, as it does for BASECOST and LVLVAL. Java builds the
        # object FROM the template and then restores the document onto it, so
        # a stated value is the last word; this loader runs the two the other
        # way round, and these three lines used to overwrite what `_init` had
        # just read. A custom power stating END="No" came back saying "Yes",
        # on 209 characters, and TARGET="N/A" came back "SELFONLY" — the
        # heuristics here ("only if empty", "only if N/A") were standing in for
        # the precedence, and could not tell a document that said "N/A" from
        # one that said nothing at all.
        #
        # Gated on the source having stated it AND this class declaring it:
        # `_source_attrs` is every attribute on the element, including ones no
        # subclass reads, and suppressing the template for an attribute that
        # was never loaded would leave the field at its constructor default.
        stated = self._stated_and_declared()
        if tmpl.uses_end and "END" not in stated:
            self.uses_end = True
        if tmpl.duration and not self._duration and "DURATION" not in stated:
            self._duration = tmpl.duration
        if tmpl.target and self.target in ("", "N/A") and "TARGET" not in stated:
            self.target = tmpl.target

    def _stated_and_declared(self) -> frozenset:
        """XML attribute names the source stated that this class also reads."""
        stated = getattr(self, "_source_attrs", None)
        if not stated:
            return frozenset()
        declared = {d.attr for d in type(self).xml_schema()}
        return frozenset(stated & declared)

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

    @property
    def sorting_value(self) -> str:
        """Java ``GenericObject.getSortingValue()`` (line 2737): ``toString()``.

        The port kept only ``Sense``'s override and dropped the base, so every
        caller that sorted a mixed adder list — ``Sense.adder_string`` above
        all — raised AttributeError the moment an adder was not a Sense.
        SenseAdder extends Power, not Sense, which is exactly that case.
        """
        return str(self)

    @property
    def alias_for_vector(self) -> str:
        """One object's contribution to an adder string.

        Java spells this as ``Adder.addAliasToVector(vec)`` (Adder.java:561),
        which appends to a caller-owned list and recurses; a property that
        returns this object's own text composes better in Python, and
        ``adder_string`` below does the recursion.
        """
        parts = []
        alias = (self.alias or "").strip()
        if alias:
            parts.append(alias)
        # The option's alias, from the resolved object where there is one and
        # from the document otherwise. This loader does not resolve option
        # objects for adders, so `_selected_option` is None on all of them and
        # this clause never fired — HD prints "Limitation Impairs Greatly
        # Impairing" where this printed "Limitation Impairs", on 2,686 adder
        # strings. OPTION_ALIAS is what HD wrote out FROM the option it had, so
        # the document carries the same string by a shorter route.
        option = self._selected_option
        option_alias = ""
        if option is not None:
            option_alias = (option.alias or "").strip()
        if not option_alias:
            option_alias = (getattr(self, "source_option_alias", "") or "").strip()
        if option_alias:
            parts.append(option_alias)
        if self.input and self.input.strip():
            parts.append(self.input.strip())
        if self._levels > 0 and "[LVL]" not in (self._display or ""):
            if self.level_power != 1:
                total = self.level_multiplier * (self.level_power ** self._levels)
                parts.append(f"x{int(total)}")
            else:
                parts.append(f"+{self._levels * self.level_multiplier}")
        return " ".join(parts)

    def get_text_output(self) -> str:
        """What the sheet shows for this object.

        Java ``GenericObject.getTextOutput()`` (line 1897). ``TEXT`` in an HDC
        file is a USER OVERRIDE — something the player typed to replace the
        generated line — not a cached render of it. When it is absent the
        object describes itself; when it is present it wins outright, and no
        amount of fixing the display layer will change what that object prints.
        """
        return self.text_output.strip() or self.column2_output

    def nameless_column2_output(self) -> str:
        """The same line without the player's own name in front of it.

        Java sets the name aside, renders, and puts it back
        (GenericObject.java:2153) — the name is prepended by the renderer, so
        the only way to omit it is to make it briefly not exist.
        """
        holder = self._name
        self._name = ""
        try:
            return self.get_text_output()
        finally:
            self._name = holder

    @property
    def modifier_string(self) -> str:
        """Every modifier this object carries, as HD writes them on the sheet.

        Ported from ``GenericObject.getModifierString`` (GenericObject.java:2062).
        Advantages first, joined with ", "; then the limitations, the first of
        which opens with "; " instead. Both groups sort by total value, and the
        active-point note sits between them.

        This was a deliberate stub returning "" for as long as ``Modifier`` had
        no ``column2_output`` of its own — a partial port would have emitted
        confidently wrong strings, which is worse than nothing. Modifier has a
        real one now, so this can do its half.
        """
        mods = list(self.assigned_modifiers)

        # A framework's limitations are shown on each slot, unless the caller
        # has turned that off. HD reads the preference; absent one, it is on,
        # which is HD's own default.
        parent = self.parent
        if parent is not None and _show_common_limitations():
            for mod in parent.assigned_modifiers:
                if "VPP" in (mod.types or []):
                    continue
                from kirby_cost.objects.frameworks import is_multipower
                if mod.xmlid == "CHARGES" and is_multipower(parent):
                    continue
                shared = (mod.total_value < 0
                          or type(parent).__name__ == "VariablePowerPool")
                already = GenericObject.find_object_by_id(
                    self._assigned_modifiers, mod.xmlid)
                generic = mod.xmlid in ("GENERIC_OBJECT", "CUSTOM_MODIFIER",
                                        "MODIFIER")
                if shared and (already is None or generic):
                    mods.append(mod)

        mods.sort(key=lambda m: m.total_value)

        ret = ""
        for mod in mods:
            if (mod.total_value >= 0 and mod.display_in_string
                    and not mod.is_limitation):
                ret += ", " + mod.column2_output

        if self.display_active_cost and (
                self.active_cost != self.total_cost
                or self.real_cost != self.total_cost):
            ret += f" ({round_up(self.active_cost)} Active Points)"

        negatives = 0
        for mod in mods:
            if (mod.total_value < 0 or mod.is_limitation) and mod.display_in_string:
                negatives += 1
                ret += "; " if negatives == 1 else ", "
                ret += mod.column2_output
        return ret

    @property
    def adder_string(self) -> str:
        """Java ``GenericObject.getAdderString()`` (line 1185).

        Adders that are themselves groups, or that offer sub-adders, sort into
        a separate list that prints first; everything else follows. Both lists
        sort case-insensitively, and blank entries drop out.

        Subclasses override this freely (Sense sorts ANALYZE after
        DISCRIMINATORY, several others return ""), but the base existed in
        Java and did not here, so Money and EnvironmentalMovement — which
        inherit it — raised AttributeError from ``column2_output``.
        """
        group_aliases: List[str] = []
        plain_aliases: List[str] = []

        def collect(adder: 'GenericObject', into: List[str]) -> None:
            # display_in_string lives on Adder; a non-Adder child defaults to shown.
            if getattr(adder, 'is_selected', True) and getattr(adder, 'display_in_string', True):
                text = adder.alias_for_vector
                if text.strip():
                    into.append(text.strip())
            for sub in adder.assigned_adders:
                collect(sub, into)

        for adder in self.assigned_adders:
            is_group = bool(adder.available_adders) or getattr(adder, 'is_group', False)
            if is_group and getattr(adder, 'is_selected', True):
                collect(adder, group_aliases)
            else:
                collect(adder, plain_aliases)

        group_aliases.sort(key=str.upper)
        plain_aliases.sort(key=str.upper)
        return ", ".join(group_aliases + plain_aliases)

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

        # The element's own TAG and XMLID, kept because they are facts of the
        # document that the class cannot re-derive. A CompoundPower is written
        # by HD as <POWER XMLID="COMPOUNDPOWER"> and a pool as
        # <VPP XMLID="GENERIC_OBJECT"> — framework identity lives in the tag,
        # and the xmlid does NOT follow from the Python class. Without these,
        # a rewrite guesses: CompoundPowers went back out as <GENERIC_OBJECT>,
        # which HERO Designer ignores inside POWERS, so a round trip through
        # our own writer silently cost Ravel two powers and 41 points. Our
        # loader read that same file back as complete, so nothing but HD itself
        # could catch it.
        self._source_tag = getattr(element, "tag", "") or ""
        self._source_xmlid = element.get("XMLID", "") or ""
        #: Which attributes the FILE actually stated. An HDC stores only
        #: overrides — precedence is XML, then the selected option, then the
        #: template — so a value that came from the template must not be
        #: written back as though the character had declared it. Doing so
        #: freezes template data into the file and the character stops
        #: following its template: writing a template-derived MINCOST="1.0"
        #: onto two of Ravel's skills made HD recost them 3 -> 2.
        #: A BuildNode (io/build_json.py) quacks like an element but has no
        #: keys(); an empty set means "no source spoke for this object", and
        #: everything it holds is then written as its own statement.
        _keys = getattr(element, "keys", None)
        #: Kept as a TUPLE, not a set: order is a fact of the document too,
        #: and lxml writes attributes in the order they were set.
        self._source_attr_order = tuple(_keys()) if callable(_keys) else ()
        self._source_attrs = frozenset(self._source_attr_order)
        #: The raw strings the document used. An attribute we did not change is
        #: echoed back exactly as written, so our formatting never introduces a
        #: difference: HD writes SELECTED="YES" and this engine would render the
        #: same boolean as "Yes" — a diff on 60 elements that means nothing.
        #: Child element tags the document carried. PROVIDES is template-
        #: derived on a sense power, and writing it back added two elements HD
        #: never wrote — the same "resolved value echoed as an override"
        #: mistake as MINCOST, one level down in the tree.
        try:
            self._source_child_tags = frozenset(c.tag for c in element)
        except TypeError:
            self._source_child_tags = frozenset()
        _get = getattr(element, "get", None)
        self._source_attr_values = (
            {k: element.get(k) for k in self._source_attr_order}
            if callable(_get) else {})

        # Everything declared in XML_ATTRS, read from one inventory that the
        # writer also uses. See kirby_cost/engine/xml_attrs.py for why this is
        # a table and not another hand-maintained list of getattr calls.
        self.read_xml_attrs(element)

        # The object's IDENTITY, when the source supplies one. Without this the
        # id is whatever `GenericObject._id_count` happened to reach while this
        # object was being constructed — unique within a process, meaningless
        # across loads. A consumer that has to find this object again then has
        # nothing to hold but the xmlid and the name, and the xmlid is a TYPE:
        # a character may carry several powers agreeing on both, so every such
        # key collides silently.
        #
        # Read on the normal load path (it was only read in
        # `read_element`, the child-descending path), so an HDC file's `ID`
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

        # ALIAS="" is a statement, not an absence. Java tests the attribute's
        # PRESENCE (`check != null && element.getAttribute("ALIAS") != null`,
        # GenericObject.java:3166) where this tested its truthiness, so an
        # explicitly blank alias was discarded and the template's own name
        # survived in its place — 74 characters exported an Enhanced Perception
        # or a Naked Modifier under a name their file had deliberately cleared.
        alias = XMLUtility.get_value(element, "ALIAS")
        if alias or "ALIAS" in getattr(self, "_source_attrs", ()):
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

        # Folded in from restore_from_save, which ran immediately after
        # _init and re-read much of what it had just read. Kept because a
        # few of these are read NOWHERE else: TEXT, USE_END_RESERVE and
        # the ALIAS -> abbreviation fallback.
        if element is None:
            return
        
        # Call _init first to handle basic initialization
        
        # Restore saved state
        alias = XMLUtility.get_value(element, "ALIAS")
        if alias:
            self._alias = alias
            self.abbreviation = alias
        elif "ALIAS" not in getattr(self, "_source_attrs", ()) and not self._alias:
            # Java falls back to the display name only when the attribute is
            # ABSENT (`else if (alias == null)`, GenericObject.java:3617). This
            # tested `not self._alias`, which cannot tell a document that
            # cleared the alias from one that never carried it — so the fix one
            # read above, where ALIAS="" is finally honoured, was undone four
            # hundred lines later by the fallback firing on the empty string.
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
    


def _show_common_limitations() -> bool:
    """Whether a framework's limitations repeat on every slot.

    HD reads this preference (GenericObject.java:2067). Defaults to True, which
    is HD's own default, so a missing preference does not silently drop
    limitations a character actually has.
    """
    try:
        from kirby_cost.core.context import EngineContext
        return bool(EngineContext.prefs().show_common_limitations)
    except Exception:  # noqa: BLE001
        return True


def option_alias(adder) -> str:
    """What HD would print for this adder's selected option.

    HD reads ``getSelectedOption().getAlias()`` — the template's option object.
    This loader never resolves that object for adders, so ``selected_option`` is
    None on every one of them and the display code below, which is a faithful
    port, had nothing to read.

    The document states the same string outright. HD writes OPTION_ALIAS from
    the option it selected, so the file's own value IS the option's alias:
    ``OPTION_ALIAS="(Frequently"`` on a Physical Complication's OCCURS adder.
    Using it is not an approximation; it is the same string by a shorter route,
    and it keeps this a display-only change. Resolving the option objects
    properly belongs in the loader, where it would also touch cost paths
    (Skill reads ``available_adders``), and that is a separate job with its own
    parity risk.
    """
    option = getattr(adder, "selected_option", None)
    if option is not None and (option.alias or "").strip():
        return option.alias
    return getattr(adder, "source_option_alias", "") or ""
