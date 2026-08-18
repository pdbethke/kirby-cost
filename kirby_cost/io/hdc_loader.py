"""
HDC Character Loader — loads an HDC file into Python GenericObject instances.

This is the bridge between the HDC XML parser and the cost calculation engine.
It constructs the correct Python subclass for each element, sets up parent-child
relationships (framework slots), and loads all modifiers and adders.

Usage:
    loader = HDCLoader()
    hero = loader.load_file("character.hdc")
    for power in hero.powers:
        print(power.xmlid, power.total_cost, power.active_cost, power.real_cost_pre_list)
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from lxml import etree
from kirby_cost.io.xml_utility import XMLUtility
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.frameworks import (
    Multipower, VariablePowerPool, ElementalControl,
)
from kirby_cost.objects.list import List
from kirby_cost.template.hdt_provider import HDTTemplateProvider
from kirby_cost.template.provider import TemplateProvider

logger = logging.getLogger(__name__)


@dataclass
class BuildNode:
    """lxml-element-compatible adapter so HDCLoader's construction core can be
    driven from a build doc (JSON) instead of XML. Implements only the element
    API the loader uses: tag, get, text, find, findall, iteration. `get()`
    returns None for a missing key (matching lxml's Element.get)."""
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    text: str | None = None

    def get(self, name, default=None):
        v = self.attrs.get(name)
        return v if v is not None else default

    def find(self, tag):
        return next((c for c in self.children if c.tag == tag), None)

    def findall(self, tag):
        return [c for c in self.children if c.tag == tag]

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)


# HDC top-level section tags that the loader explicitly parses.
# Any root child tag NOT in this set will be collected in
# LoadedHero.unparsed_sections so callers can see what the loader skipped.
_KNOWN_SECTIONS = {
    "CHARACTER_INFO", "BASIC_CONFIGURATION", "CHARACTERISTICS", "SKILLS",
    "PERKS", "TALENTS", "MARTIALARTS", "POWERS", "EQUIPMENT",
    "DISADVANTAGES", "RULES", "IMAGE", "TEMPLATE",
}

# Map HDC framework tag to the real Python class. Before this refactor the
# loader built every framework as a generic _FallbackObject and relied on
# string xmlid matching; now it instantiates the proper subclass so
# isinstance() checks in the engine are type-safe.
_FRAMEWORK_CLASSES = {
    "MULTIPOWER": Multipower,
    "VPP": VariablePowerPool,
    "ELEMENTALCONTROL": ElementalControl,
    "LIST": List,
}


# ═══════════════════════════════════════════════════════════
#  HDT Template — the source of truth for all cost definitions
# ═══════════════════════════════════════════════════════════

# Types from the template's <TYPE> child elements, for the handful of
# skills/perks whose types a TemplateData does not carry. They decide Enhancer
# cost-savings matching (Scholar->KNOWLEDGE, Scientist->SCIENCE, etc.).
_HDT_TYPES: dict[str, list[str]] = {
    # Skills
    "KNOWLEDGE_SKILL":    ["KNOWLEDGE"],
    "SCIENCE_SKILL":      ["SCIENCE"],
    "PROFESSIONAL_SKILL": ["PROFESSIONAL"],
    "LANGUAGES":          ["LANGUAGE"],
    "AREA_KNOWLEDGE":     ["AREA"],
    "CONTACT":            ["CONTACT"],
    # Enhancers (so they get their applicable types)
    "SCHOLAR":            ["KNOWLEDGE"],
    "SCIENTIST":          ["SCIENCE"],
    "JACK_OF_ALL_TRADES": ["PROFESSIONAL"],
    "LINGUIST":           ["LANGUAGE"],
    "TRAVELER":           ["AREA"],
    "WELL_CONNECTED":     ["CONTACT"],
    # Characteristics and powers/talents with DEFENSE type (from Main6E.hdt)
    # — needed for Automaton defense cost multiplier.
    "PD":                 ["DEFENSE"],
    "ED":                 ["DEFENSE"],
    "COMBAT_LUCK":        ["DEFENSE"],
    "FORCEWALL":          ["STANDARD", "DEFENSE"],
    "DAMAGENEGATION":     ["STANDARD", "DEFENSE"],
    "DAMAGEREDUCTION":    ["STANDARD", "DEFENSE"],
    "MISSILEDEFLECTION":  ["STANDARD", "DEFENSE"],
    "FLASHDEFENSE":       ["SPECIAL", "DEFENSE"],
    "KBRESISTANCE":       ["SPECIAL", "DEFENSE"],
    "MENTALDEFENSE":      ["SPECIAL", "DEFENSE"],
    "POWERDEFENSE":       ["SPECIAL", "DEFENSE"],
    "FORCEFIELD":         ["STANDARD", "DEFENSE"],
}

# Adder-based skills whose adders all have MINCOST=1 in the template.
# ``AdderTemplate`` carries no minimum cost, so it is applied here.
# This minimum cost is used by the n-counter logic in skill subclasses
# (Navigation, AnimalHandler, Weaponsmith, etc.) to discount adders beyond
# the first one.
_ADDER_MINCOST_SKILLS: set[str] = {
    "NAVIGATION", "ANIMAL_HANDLER", "GAMBLING", "WEAPONSMITH", "FORGERY",
    "ELECTRONICS", "COMPUTER_PROGRAMMING", "SYSTEMS_OPERATION", "SURVIVAL",
}

# Adder option costs not carried by an ``AdderTemplate``.
# Maps (parent_xmlid, adder_xmlid, option_id) → base_cost.
# The Java template has these as option entries on adders, but the dump
# doesn't export them.  Used to correct stale XML BASECOST values.
_ADDER_OPTION_COSTS: dict[tuple[str, str, str], float] = {
    # Life Support → Immunity options (from Main6E.hdt)
    ("LIFESUPPORT", "IMMUNITY", "UNCOMMON"):     3.0,
    ("LIFESUPPORT", "IMMUNITY", "ALCOHOL"):      3.0,
    ("LIFESUPPORT", "IMMUNITY", "COMMON"):       5.0,
    ("LIFESUPPORT", "IMMUNITY", "ALLDISEASE"):   5.0,
    ("LIFESUPPORT", "IMMUNITY", "ALLPOISON"):    5.0,
    ("LIFESUPPORT", "IMMUNITY", "VERYCOMMON"):   10.0,
    ("LIFESUPPORT", "IMMUNITY", "ALL"):          15.0,
}

# Modifier types from Main6E.hdt <TYPE> child elements.
# These are needed for cost calculation filtering (e.g. VPP modifiers
# should not propagate to slot active costs).
_MODIFIER_TYPES: dict[str, list[str]] = {
    "HALFPHASE":  ["VPP"],
    "ZEROPHASE":  ["VPP"],
    "NOSKILLROLL": ["VPP"],
}

# Sense template PROVIDES from Main6E.hdt.
# These are capabilities built into each sense type's definition.
# Used by Sense.total_cost to compute the 6E sense group deduction.
_SENSE_TEMPLATE_PROVIDES: dict[str, list[str]] = {
    "DETECT":               ["ENHANCEDPERCEPTION"],
    "ACTIVESONAR":          ["TARGETINGSENSE"],
    "HRRP":                 ["INCREASEDARC240", "INCREASEDARC360", "TRANSMIT"],
    "MENTALAWARENESS":      ["MAKEASENSE"],
    "RADAR":                ["TARGETINGSENSE"],
    "RADIOPERCEPTION":      ["INCREASEDARC240", "INCREASEDARC360"],
    "RADIOPERCEIVETRANSMIT":["INCREASEDARC240", "INCREASEDARC360", "TRANSMIT"],
    "SPATIALAWARENESS":     ["TARGETINGSENSE", "MAKEASENSE", "PENETRATIVE"],
    # Built-in senses (from SENSE elements in the template)
    "NORMALHEARING":        ["INCREASEDARC240", "INCREASEDARC360"],
    "NORMALSMELL":          ["RANGE", "INCREASEDARC240", "INCREASEDARC360"],
    "DANGER_SENSE":         ["RANGE", "INCREASEDARC240", "INCREASEDARC360"],
    "COMBAT_SENSE":         ["TARGETINGSENSE", "RANGE", "INCREASEDARC240", "INCREASEDARC360"],
    "MINDSCAN":             ["RANGE", "INCREASEDARC240", "INCREASEDARC360",
                             "TARGETINGSENSE", "DISCRIMINATORY"],
}

# Power-specific modifiers not in the global template.
# Defined inside specific power entries in Main6E.hdt (HKA, RKA).
_POWER_SPECIFIC_MODIFIERS: dict[str, dict] = {
    "INCREASEDSTUNMULTIPLIER": {
        "base_cost": 0.0,
        "level_cost": 0.25,
        "level_value": 1.0,
        "min_set": True,
        "minimum_cost": 0.25,
        "max_set": True,
        "max_cost": 10.0,
    },
    "DECREASEDSTUNMULTIPLIER": {
        "base_cost": 0.0,
        "level_cost": -0.25,
        "level_value": 1.0,
        "min_set": True,
        "minimum_cost": -10.0,
        "max_set": True,
        "max_cost": -0.25,
    },
    "NOSTRBONUS": {
        "base_cost": -0.5,
        "level_cost": 0.0,
        "level_value": -1.0,
        "min_set": True,
        "minimum_cost": -10.0,
        "max_set": True,
        "max_cost": 10.0,
    },
    "RAPIDDUPLICATION": {
        "base_cost": 0.0,
        "level_cost": 0.25,
        "level_value": 1.0,
    },
    "ALTEREDDUPLICATES": {
        "base_cost": 0.0,
        "level_cost": 0.25,
        "level_value": 1.0,
    },
}




class LoadedHero:
    """Container for a loaded character's objects.

    Consumer caveat: ``HDCLoader.load_file`` installs this hero as the global
    active hero (via ``EngineContext.set_active_hero``).  Maneuver and
    STR-dependent costs are evaluated lazily against the active hero, so
    evaluate one hero's costs before loading the next.  Multi-hero consumers
    must re-set the active hero (``EngineContext.set_active_hero(hero)``) before
    reading costs after any subsequent load.
    """

    def __init__(self):
        self.name: str = ""
        self.template_name: str = ""

        # Document-level facts. The character object is meant to be the full
        # shape of the HDC in class form — everything downstream (a relational
        # projection, an exporter) reads the object, never the file. Anything
        # the document states that the object cannot hold is a hole: a writer
        # would have to invent the value, and a round trip would lose it.
        #: The CHARACTER element's own version attribute.
        self.version: str = "6.0"
        #: BASIC_CONFIGURATION/EXPORT_TEMPLATE — the print template last used.
        self.export_template: str = ""
        #: How the file was encoded on disk. HD writes UTF-16; the loader used
        #: to detect this and throw it away, so a rewrite could only guess.
        self.source_encoding: str = ""
        #: BASIC_CONFIGURATION/RULES — the campaign ruleset's NAME, when the
        #: document names it there. Held rather than assumed: the writer used
        #: to emit RULES="Default" unconditionally, which invented the
        #: attribute on the 133 characters whose files never stated it.
        self.rules_name: str = ""
        #: The campaign <RULES> block exactly as the document stated it, in
        #: order. HD writes the whole ruleset into the file — some 70
        #: attributes, from BASEPOINTS and APPEREND through the skill-roll
        #: denominators to the five notes labels — and the engine reads one of
        #: them. The other 69 were dropped on write, so every character with a
        #: campaign block reloaded onto HD's defaults instead of its campaign:
        #: 102 characters silently changed ruleset.
        #:
        #: Kept verbatim rather than modelled onto `Rules`. These are campaign
        #: CONFIGURATION, not character state; porting 70 fields the engine
        #: does not consult would be 70 more places to drift, and the point of
        #: holding them is that the document said them. The handful the engine
        #: does act on are parsed onto `Rules` as before, from this same block.
        self.rules_attrs: dict[str, str] = {}

        # Character identification
        self.player_name: str = ""
        self.alternate_identities: str = ""
        self.campaign_name: str = ""
        self.genre: str = ""
        self.gm: str = ""

        # Point totals
        self.base_points: int = 400
        self.disad_points: int = 75
        self.experience: int = 0

        # Physical description
        self.height: float = 0.0  # inches
        self.weight: float = 0.0  # pounds
        self.hair_color: str = ""
        self.eye_color: str = ""

        # Biography text fields
        self.appearance: str = ""
        self.background: str = ""
        self.personality: str = ""
        self.quote: str = ""
        self.tactics: str = ""
        self.campaign_use: str = ""

        # Notes
        self.notes1: str = ""
        self.notes2: str = ""
        self.notes3: str = ""
        self.notes4: str = ""
        self.notes5: str = ""

        # Image
        self.image_data: str = ""  # base64 encoded
        self.image_filename: str = ""

        # Object lists
        self.characteristics: list[GenericObject] = []
        self.powers: list[GenericObject] = []
        self.skills: list[GenericObject] = []
        self.perks: list[GenericObject] = []
        self.talents: list[GenericObject] = []
        self.complications: list[GenericObject] = []
        self.equipment: list[GenericObject] = []
        self.martial_arts: list[GenericObject] = []
        self.unparsed_sections: list[str] = []  # sections present in the HDC that the loader does not parse; populated by load_file (Task 4), empty until then
        # Computed characteristic values (for addModifiersToBase)
        self._char_values: dict[str, float] = {}
        # Rules (6E defaults)
        from kirby_cost.model.rules import Rules
        self.rules: Rules = Rules()

    def compute_characteristic_values(self, provider: Optional[TemplateProvider] = None) -> None:
        """
        Compute base characteristic values (characteristic section only).

        Sums the 6E base values plus levels from the CHARACTERISTICS section.
        Does NOT include power-based characteristic purchases, because Java's
        addModifiersToBase uses the hero's base characteristic value, not the
        total from all sources.

        Base values come from the supplied ``TemplateProvider`` (or a
        default ``HDTTemplateProvider`` if none is given) — they are
        NOT hardcoded. This honours per-template starting values: a
        Vehicle6E character's PD/ED/SPD bases differ from a Heroic6E
        character's, and both flow from the template, not from a
        constant table. The set of characteristics considered is
        whatever ``self.characteristics`` carries, plus the three
        movement powers (RUNNING/SWIMMING/LEAPING) which are baseline
        on every character.
        """
        if provider is None:
            provider = HDTTemplateProvider()

        def _base_for(xmlid: str) -> float:
            td = provider.get_template_data(xmlid)
            if td is None:
                return 0.0
            return float(td.base_value)

        self._char_values = {}
        # Seed base values from the provider for every characteristic
        # the character actually carries.
        for c in self.characteristics:
            self._char_values[c.xmlid] = _base_for(c.xmlid)
        # RUNNING / SWIMMING / LEAPING are implicit baseline on every
        # character (HDC files don't list them unless purchased).
        for movement in ("RUNNING", "SWIMMING", "LEAPING"):
            self._char_values.setdefault(movement, _base_for(movement))

        # Add levels from characteristics section only
        for c in self.characteristics:
            self._char_values[c.xmlid] = self._char_values.get(c.xmlid, 0.0) + c.levels

    def characteristic_value(self, xmlid: str) -> float:
        """Get the total value of a characteristic (base + all purchased levels)."""
        if not self._char_values:
            self.compute_characteristic_values()
        return self._char_values.get(xmlid, 0.0)

    @property
    def maneuvers(self) -> list[GenericObject]:
        """Java name for the martial-arts list (Hero.getManeuvers)."""
        return self.martial_arts

    def characteristic(self, char_type: int) -> Optional[GenericObject]:
        """Get a characteristic by Java Constants type integer.

        Uses the ported Java Constants contract via
        ``kirby_cost.util.constants.characteristic_string``:
        1=STR, 2=DEX, 3=CON, 4=BODY, 5=INT, 6=EGO, 7=PRE, 9=PD, 10=ED,
        11=SPD, 12=REC, 13=END, 14=STUN, 30=OCV, 31=DCV, 32=OMCV, 33=DMCV
        (plus COM=8, movement types 17-19, and CUSTOM* 20-29).

        Returns the first matching characteristic, or None if *char_type* is
        unknown or no characteristic with that XMLID is present.

        Note: Java's ``Hero.getCharacteristic`` returns the *last* match;
        this returns the *first* — only differs when duplicate custom
        characteristics share an XMLID, which cannot happen in well-formed HDC
        files.
        """
        from kirby_cost.util.constants import characteristic_string
        xmlid = characteristic_string(char_type)
        # characteristic_string returns "GENERAL" for unknown types; treat that
        # as "not found" unless char_type actually IS CharacteristicType.GENERAL.
        if xmlid == "GENERAL" and char_type != 0:
            return None
        for c in self.characteristics:
            if c.xmlid == xmlid:
                return c
        return None

    @property
    def disads_used(self) -> int:
        """Total complication points (Java Hero.getDisadsUsed)."""
        return sum(int(d.real_cost) for d in self.complications)

    @property
    def total_points(self) -> float:
        """Total points spent (Java Hero meta loop: chars+skills+perks+talents+maneuvers+powers).

        A power sitting in a Variable Power Pool contributes nothing: the pool
        already bought the capacity, and Java prices its slots at zero toward
        the character with `VariablePowerPool.getRealCostForChild()` returning
        a flat `0` (against Multipower's slot arithmetic, which does charge).

        This is applied here rather than in `VariablePowerPool
        .real_cost_for_child` because the two readings differ. A slot's own
        reported cost is NOT zero — the oracle dumps MENTON's Ego Attack at 150
        and the engine agrees — but `real_cost` on a child delegates to the
        parent (`engine/cost.py:175`), so zeroing that method would collapse
        every slot's reported cost as well. Only the total omits them:
        MENTON-CV1 is 841 unparented powers + 683 elsewhere = 1524, with its 13
        slots (1313 points) appearing nowhere.
        """
        from kirby_cost.objects.frameworks import is_vpp

        total = 0.0
        for lst in (self.characteristics, self.skills, self.perks,
                    self.talents, self.martial_arts, self.powers):
            for obj in lst:
                parent = getattr(obj, "parent", None)
                if parent is not None and is_vpp(parent):
                    continue
                total += obj.real_cost
        return total

    @property
    def available_points(self) -> float:
        """base + disads used + experience - spent."""
        return self.base_points + self.disads_used + self.experience - self.total_points


def _hold_slot(framework: GenericObject, slot: GenericObject) -> None:
    """Record *slot* on *framework* as well as linking it upward.

    ``List.objects`` is Java's ``getObjects()``, and rules ask a container
    about its contents through it: ``Charges.parentUsesEND()`` decides whether
    a Multipower reserve uses END by asking its slots, because the reserve
    never does itself (``Charges.java:450-470``). Linking only upward left
    every framework reporting an empty pool, so that question always answered
    "no" and clamped the modifier away.

    Only real ``List`` subclasses carry the collection; anything else linked as
    a parent (an Enhancer-style Skill, say) is left alone.
    """
    from kirby_cost.objects.list import List as _List

    if not isinstance(framework, _List):
        return
    # add_object dedups on id, so re-linking the same slot is harmless.
    framework.add_object(slot)


class _FallbackObject(GenericObject):
    """Fallback for unknown XMLIDs."""
    pass




class HDCLoader:
    """Loads HDC files into Python objects with proper cost calculations.

    Args:
        provider: source of template cost data.  Defaults to
            ``HDTTemplateProvider`` (reads the user's own ``.hdt``, resolved
            from ``KIRBY_COST_HDT``).  Pass any other implementation of the
            ``TemplateProvider`` protocol to drive lookups from elsewhere —
            a relational catalogue, say.
        strict: if True, a registered class that fails to construct raises
            instead of silently falling back to ``_FallbackObject``.  Defaults
            to False (the failure is logged at ERROR but loading continues).
    """

    def __init__(self, provider: Optional[TemplateProvider] = None,
                 strict: bool = False):
        self._provider: TemplateProvider = provider or HDTTemplateProvider()
        self._registry_loaded: bool = False
        # True unless a loaded character omitted its TEMPLATE attribute.
        self._character_has_template: bool = True
        self._char_map: Optional[dict] = None
        self._strict: bool = strict

    # ── Template lookup (delegates to provider) ────────────────────────

    @property
    def _provider_in_use(self):
        """The template this character is costed against.

        Defaults to the configured provider until a character declares one —
        see the note where hero.template_name is read.
        """
        return getattr(self, "_active_provider", None) or self._provider

    def _get_template_data(self, xmlid: str) -> Optional["TemplateData"]:
        """Look up a TemplateData by XMLID via the active provider."""
        return self._provider_in_use.get_template_data(xmlid)

    def _get_maneuver_template(self, display: str) -> Optional["TemplateData"]:
        """Look up a maneuver's TemplateData by its DISPLAY.

        A maneuver has no xmlid of its own: the template writes
        ``<MANEUVER DISPLAY="Killing Strike">`` with no XMLID attribute, and
        the character writes ``<MANEUVER XMLID="MANEUVER" DISPLAY="Killing
        Strike">``. Java therefore matches maneuvers on display alone
        (``Hero.java:2706-2731``), where every other section matches on xmlid.

        None means the template defines no such maneuver, which in Java is a
        custom maneuver — built from the HDC element and nothing else.
        """
        getter = getattr(self._provider_in_use, "get_maneuver", None)
        if getter is None:
            return None
        return getter(display)

    # ── Template application helpers ───────────────────────────

    def _apply_template_defaults(self, obj: GenericObject, xmlid: str, option_id: str = None) -> None:
        """Apply template defaults to an object, including HDT types."""
        # Maneuvers are the one section keyed by display rather than xmlid —
        # every one of them arrives as XMLID="MANEUVER", so an xmlid lookup
        # dresses all 53 in whichever the template states first (Basic Strike).
        if xmlid == "MANEUVER":
            tmpl = self._get_maneuver_template(getattr(obj, "display", "") or "")
            # Java does not build a maneuver from the character's element and
            # then dress it: it clones the template's own Maneuver — base cost
            # and all, already read from <MANEUVER BASECOST="4"> — and calls
            # restoreFromSave on the clone (Hero.java:2713-2716). So the
            # template's cost is the starting point and an HDC BASECOST
            # overrides it, rather than being the only source. Maneuver._init's
            # baseCost = 3 (Maneuver.java:417) is the *custom* maneuver's
            # default, which is why a template match must replace it.
            if tmpl is not None and not obj._base_cost_from_xml:
                obj.base_cost = tmpl.base_cost
        else:
            tmpl = self._get_template_data(xmlid)
        if tmpl is None:
            return

        # No template on the character => no sense groups exist. Java falls back
        # to the single-sense option; resolve it through the template's OWN "*"
        # alias rather than hardcoding a target. Measured over 655 oracle
        # fixtures: 72/72 template-bearing GROUP options take the group rate,
        # 1/1 without a template takes the single rate (UNDEAD_GHOUL).
        if (option_id
                and option_id.upper().endswith("GROUP")
                and not getattr(self, "_character_has_template", True)
                and getattr(tmpl, "option_aliases", None)):
            fallback = tmpl.option_aliases.get("*")
            if fallback:
                option_id = fallback

        obj.apply_template(tmpl, option_id)

        # Apply HDT types (KNOWLEDGE, SCIENCE, PROFESSIONAL, etc.) so that
        # Enhancer cost-savings matching works correctly.
        hdt_types = _HDT_TYPES.get(xmlid)
        if hdt_types:
            for t in hdt_types:
                if t not in obj._types:
                    obj._types.append(t)

    def _apply_template_to_modifier(self, mod: Modifier, xmlid: str, option_id: str = None) -> None:
        """Apply template defaults to a modifier."""
        tmpl = self._get_template_data(xmlid)
        if tmpl is None:
            return
        mod.apply_template(tmpl, option_id)

    def _apply_template_to_adder(self, adder: Adder, parent_xmlid: str, adder_xmlid: str,
                                  option_id: str = None) -> None:
        """Apply template defaults to an adder from parent's adder definitions."""
        tmpl = self._get_template_data(parent_xmlid)
        if tmpl is None:
            # Even without a template, apply MINCOST for adder-based skills
            if not adder.min_set and parent_xmlid in _ADDER_MINCOST_SKILLS:
                adder.minimum_cost = 1.0
                adder.min_set = True
            return

        adder_tmpl = tmpl.adders.get(adder_xmlid)
        if adder_tmpl is None:
            if not adder.min_set and parent_xmlid in _ADDER_MINCOST_SKILLS:
                adder.minimum_cost = 1.0
                adder.min_set = True
            return

        # Option-specific cost override (e.g. IMMUNITY ALCOHOL=3)
        if option_id:
            option_cost = _ADDER_OPTION_COSTS.get(
                (parent_xmlid, adder_xmlid, option_id))
            if option_cost is not None:
                adder.base_cost = option_cost

        # Apply adder template (cost fields + types)
        adder.apply_adder_template(adder_tmpl)

        # Apply minimum cost from MINCOST skills
        if not adder.min_set and parent_xmlid in _ADDER_MINCOST_SKILLS:
            adder.minimum_cost = 1.0
            adder.min_set = True

    def _apply_adder_types(self, adder: Adder) -> None:
        """Apply types to an adder (and nested adders) from the adder_types map.

        The HDT template defines TYPE elements on adders, stored in the provider's
        adder_types lookup.  This covers nested adders that aren't in the
        parent's 'adders' dict.
        """
        provider = self._provider_in_use
        adder_type_map = (
            provider.get_adder_type_map()
            if hasattr(provider, "get_adder_type_map")
            else {}
        )
        self._apply_adder_types_recursive(adder, adder_type_map)

    @staticmethod
    def _apply_adder_types_recursive(adder: Adder, adder_type_map: dict) -> None:
        """Recursively apply types from the adder_types map."""
        if not adder.types:
            types = adder_type_map.get(adder.xmlid)
            if types:
                adder.types = list(types)
        for sub in adder.assigned_adders:
            HDCLoader._apply_adder_types_recursive(sub, adder_type_map)

    # ── Registry-based lookup (instance-cached) ──────────────────

    def _ensure_registry_loaded(self) -> None:
        """Import all subclass modules so __init_subclass__ populates the registry."""
        if self._registry_loaded:
            return
        import kirby_cost.objects._registry_imports  # noqa: F401
        self._registry_loaded = True

    def _get_power_cls(self, xmlid: str):
        """Look up a power/perk class via the __init_subclass__ registry.

        Returns None if nothing is registered for *xmlid*, letting the caller
        fall back to _FallbackObject.  Power, Perk and Talent subclasses are
        returned — the TALENTS section is loaded via obj_type="power", so
        Talent classes must be accepted here.  GenericObject subclasses that
        are registered directly (e.g. martial-arts Maneuver, ExtraDamageClasses)
        are also returned so the loader can instantiate them for sections that
        use the "power" dispatch path.  Other categories (Characteristic, Skill)
        use their own lookup paths.
        """
        from kirby_cost.objects.powers.power import Power
        from kirby_cost.objects.perks.perk import Perk
        from kirby_cost.objects.talents.talent import Talent
        from kirby_cost.objects.skills.skill import Skill
        from kirby_cost.objects.characteristics.characteristic import Characteristic
        self._ensure_registry_loaded()
        cls = GenericObject._registry.get(xmlid)
        if cls is None:
            return None
        # Accept Power/Perk/Talent (primary dispatch targets) and any other
        # registered GenericObject subclass that is not a Skill, Characteristic,
        # or Modifier (those have dedicated lookup paths and must not be
        # redirected here).
        if issubclass(cls, (Power, Perk, Talent)):
            return cls
        if not issubclass(cls, (Skill, Characteristic, Modifier)):
            return cls
        return None

    def _get_skill_cls(self, xmlid: str):
        """Look up a skill class via the __init_subclass__ registry.

        Returns None if nothing is registered for *xmlid*, letting the caller
        fall back to the base Skill class.  Mirrors _get_power_cls().
        """
        from kirby_cost.objects.skills.skill import Skill
        self._ensure_registry_loaded()
        cls = GenericObject._registry.get(xmlid)
        if cls and issubclass(cls, Skill):
            return cls
        return None

    def _get_char_map(self) -> dict:
        if self._char_map is not None:
            return self._char_map

        self._char_map = {}
        try:
            from kirby_cost.objects.characteristics.characteristic import Characteristic
            # All characteristics use the same base class for cost
            self._char_map["_DEFAULT"] = Characteristic
        except ImportError:
            pass
        return self._char_map

    # ── Public API ─────────────────────────────────────────────

    def load_file(self, file_path: str) -> LoadedHero:
        """Load an HDC file and return a LoadedHero with all objects constructed."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"HDC file not found: {file_path}")

        # Parse XML (handle UTF-16)
        with open(path, 'rb') as f:
            raw = f.read()

        # Detect encoding. Recorded on the hero (below) rather than discarded:
        # writing a UTF-16 file back out as UTF-8 is a silent change to the
        # document, and the object is supposed to carry the whole document.
        if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
            text, source_encoding = raw.decode('utf-16'), 'utf-16'
        elif raw[:4] == b'<\x00?\x00':
            text, source_encoding = raw.decode('utf-16-le'), 'utf-16-le'
        elif raw[:4] == b'\x00<\x00?':
            text, source_encoding = raw.decode('utf-16-be'), 'utf-16-be'
        else:
            text, source_encoding = raw.decode('utf-8'), 'utf-8'
        self._source_encoding = source_encoding

        # Strip XML declaration if present (lxml handles it, but encoding may conflict)
        if text.startswith('<?xml'):
            text = text[text.index('?>') + 2:].lstrip()

        root = etree.fromstring(text.encode('utf-8'))
        # HDC = <CHARACTER>, HDP prefab = <PREFAB>. Same child structure
        # (BASIC_CONFIGURATION, CHARACTERISTICS, POWERS, ...), so the rest
        # of this loader works on either. Accept both.
        if root.tag not in ("CHARACTER", "PREFAB"):
            raise ValueError(
                f"Invalid HDC/HDP: root must be CHARACTER or PREFAB, got {root.tag}"
            )

        return self._build_hero_from_root(root)

    def _build_hero_from_root(self, root) -> "LoadedHero":
        """Construct and cost a LoadedHero from any element-like root.

        The root element itself is accessed only via ``.get(attr)`` and
        ``.find(tag)``; ``.findall``, ``.tag``, ``.text``, and iteration are
        used only on the *child* elements those calls return, not on root
        directly.  A stub root therefore only needs to implement ``.get`` and
        ``.find``; the richer lxml interface is required only of its
        descendants.

        This means the method does not have to be called from load_file — it
        accepts any in-memory element tree (test fixtures, XML constructed
        without touching the filesystem, etc.) and applies the full
        construction/costing pipeline to it, making it possible to exercise
        the logic without file I/O.

        Nothing inside this method was modified during the extraction; the
        block was moved verbatim from load_file so that the Java-oracle cost
        suite remains the authoritative correctness guard.
        """
        # Reset Language similarity state between loads
        from kirby_cost.objects.skills.language import Language as _LangCls
        _LangCls.global_exclude = None
        _LangCls.number_languages_purchased = 0

        # Reset SenseGroup caches to avoid leaking hero state between loads
        from kirby_cost.objects.powers.sense_group import SenseGroup
        for group in SenseGroup.all_groups():
            group._sense_adders_saver = None
            group._sense_adders_last_call = 0.0
            group._sense_adders_has_hero = False
            if hasattr(group, '_loaded_hero'):
                group._loaded_hero = None

        hero = LoadedHero()

        # Ensure 6E sense groups are initialised (template data from Main6E.hdt).
        # These are static objects needed by Sense.get_group() and get_total_cost().
        from kirby_cost.objects.powers.sense_group import SenseGroup
        if not SenseGroup.all_groups():
            SenseGroup.clear()

        # Cost this character against the template it declares.
        #
        # HD loads the named template and costs against it, and every
        # specialised template is a thin override layer over Main6E
        # (extends="builtIn.Main6E.hdt"): Vehicle6E restates FLIGHT as
        # USESEND="No" and defines SIZE, Automaton6E prices EGO at 2/level,
        # Computer6E defines PROGRAM. Ignoring the attribute costed every
        # character against one template and was patched over, badly, by a
        # hand-rolled _apply_vehicle6e_overrides.
        #
        # It went unnoticed because the Java oracle had the same bug from the
        # other end — the headless fork could not resolve builtIn. names and
        # silently kept its Main6E bootstrap, so the fixtures agreed with an
        # engine that also ignored the attribute. Fixing the oracle moved 8 of
        # 655 fixtures. See tests/test_character_declared_template.py.
        #
        # A provider that cannot resolve the name returns itself, which is what
        # HD does: keep the active template rather than fail the load.
        hero.template_name = root.get("TEMPLATE", "")
        hero.version = root.get("version", "6.0")
        hero.source_encoding = getattr(self, "_source_encoding", "")
        switch = getattr(self._provider, "for_template", None)
        self._active_provider = (
            switch(hero.template_name) if switch is not None else self._provider
        )

        # The language similarity chart is template data too, and Language
        # reads it off the class. Refresh it for whichever template this
        # character resolved to; it used to be a JSON extract shipped in the
        # package (see load_language_chart).
        from kirby_cost.objects.skills.language import Language, load_language_chart
        Language.chart = load_language_chart(self._provider_in_use)
        # Sense GROUPS are defined by the template. A character file with no
        # TEMPLATE has none, so Java cannot resolve e.g. SMELLGROUP as a group
        # and charges the single-sense rate. Recorded here for
        # _apply_template_defaults; see tests/test_sense_group_without_template.py.
        self._character_has_template = bool(hero.template_name)

        # Character info (name, physical description, biography)
        info = root.find("CHARACTER_INFO")
        if info is not None:
            hero.name = info.get("CHARACTER_NAME", "")
            hero.player_name = info.get("PLAYER_NAME", "")
            hero.alternate_identities = info.get("ALTERNATE_IDENTITIES", "")
            hero.campaign_name = info.get("CAMPAIGN_NAME", "")
            hero.genre = info.get("GENRE", "")
            hero.gm = info.get("GM", "")

            # Physical description
            height_str = info.get("HEIGHT", "")
            hero.height = float(height_str) if height_str else 0.0
            weight_str = info.get("WEIGHT", "")
            hero.weight = float(weight_str) if weight_str else 0.0
            hero.hair_color = info.get("HAIR_COLOR", "")
            hero.eye_color = info.get("EYE_COLOR", "")

            # Biography text fields (child elements)
            # Not `field` — that shadows the dataclasses import used above.
            for tag in ("BACKGROUND", "PERSONALITY", "QUOTE", "TACTICS",
                        "CAMPAIGN_USE", "APPEARANCE",
                        "NOTES1", "NOTES2", "NOTES3", "NOTES4", "NOTES5"):
                elem = info.find(tag)
                if elem is not None and elem.text:
                    setattr(hero, tag.lower(), elem.text)

        # Basic configuration (point totals)
        basic_config = root.find("BASIC_CONFIGURATION")
        if basic_config is not None:
            bp = basic_config.get("BASE_POINTS", "")
            hero.base_points = int(bp) if bp else 400
            dp = basic_config.get("DISAD_POINTS", "")
            hero.disad_points = int(dp) if dp else 75
            xp = basic_config.get("EXPERIENCE", "")
            hero.experience = int(xp) if xp else 0
            hero.export_template = basic_config.get("EXPORT_TEMPLATE", "")
            hero.rules_name = basic_config.get("RULES", "")

        # Image data
        image_elem = root.find("IMAGE")
        if image_elem is not None:
            hero.image_filename = image_elem.get("FILENAME", "")
            hero.image_data = image_elem.text or ""

        # Load rules from HDC (language similarities, etc.). The whole block is
        # kept so the writer can state it back; only what the engine acts on is
        # parsed onto Rules.
        rules_elem = root.find("RULES")
        if rules_elem is not None:
            hero.rules_attrs = dict(rules_elem.attrib)
            lang_sim = rules_elem.get("LANGUAGESIMILARITIESUSED", "")
            if lang_sim.strip().upper().startswith("Y"):
                hero.rules._language_similarities_used = True

        # Load each section.
        #
        # CHARACTERISTICS is gated like the rest. Java reaches the same place
        # from the other direction: it walks the hero's characteristic set,
        # built from the loaded template, and pulls each one OUT of the section
        # by name (Hero.java:2472-2481), so a file element the template does
        # not define is never read at all. Enumerating the file instead costed
        # whatever it found — the four corpus vehicles carry <SIZE LEVELS="4">,
        # which Main6E.hdt does not define (only Vehicle6E.hdt does), and the
        # engine charged 15/level for it against the oracle's nothing.
        #
        # This reverses an older note that characteristics "must stay ungated".
        # That was measured against the JSON template dump; against a real .hdt
        # all 20 standard 6E characteristics resolve and only SIZE does not.
        # tests/test_characteristics_come_from_the_template.py pins the premise
        # so this cannot silently start gutting heroes if coverage regresses.
        hero.characteristics = self._load_section(root, "CHARACTERISTICS", None, "char")
        hero.powers = self._load_powers_section(root)
        hero.skills = self._load_section(root, "SKILLS", None, "skill")
        hero.perks = self._load_section(root, "PERKS", None, "power")
        hero.talents = self._load_section(root, "TALENTS", None, "power")
        hero.complications = self._load_section(root, "DISADVANTAGES", None, "disad")
        hero.martial_arts = self._load_section(root, "MARTIALARTS", None, "power",
                                               gate_on_template=False)
        # Equipment loads into its OWN list, never into hero.powers, because
        # total_points (the Java meta loop) must not count it. HD's Equipment
        # tab is by definition for gear "that does not cost Character Points"
        # (Hero Designer Documentation p14); 6E1 p34 says the same for Heroic
        # campaigns. The item still carries its engine-computed real_cost --
        # the item has a cost, the character just does not pay it.
        hero.equipment = self._load_powers_section(root, "EQUIPMENT")

        # Post-load: compute characteristic values and wire hero reference
        hero.compute_characteristic_values()
        self._wire_hero_reference(hero)

        # No per-character template emulation: see the note on
        # _apply_vehicle6e_overrides. HD costs a character against the
        # template it has loaded, not the one the file names.

        # Collect HDC sections the loader doesn't parse, so callers can see
        # what was skipped.
        hero.unparsed_sections = sorted(
            {child.tag for child in root if child.tag not in _KNOWN_SECTIONS}
        )

        # Mirror the Java CLI: HeroDesigner.activeHero = hero. Maneuver cost
        # math (STR adds, EXTRADC damage classes) dereferences the active hero.
        # NOTE: costs are lazy — callers must evaluate one hero's costs before
        # loading the next (the oracle harness already does).
        from kirby_cost.core.context import EngineContext
        EngineContext.set_active_hero(hero)

        return hero

    def _wire_hero_reference(self, hero: LoadedHero) -> None:
        """Set hero reference on all objects for enhancer lookups and characteristic rolls.

        Uses _hero for Characteristics (needed for addModifiersToBase roll calculations)
        and _loaded_hero on ALL objects for enhancer cost-savings lookups.
        """
        from kirby_cost.objects.characteristics.characteristic import Characteristic
        from kirby_cost.objects.powers.compound_power import CompoundPower
        for obj_list in (hero.characteristics, hero.powers, hero.skills,
                         hero.perks, hero.talents, hero.complications):
            for obj in obj_list:
                obj._loaded_hero = hero
                if isinstance(obj, Characteristic):
                    obj._hero = hero
                elif isinstance(obj, CompoundPower):
                    for sub in obj.powers:
                        sub._loaded_hero = hero
                        if isinstance(sub, Characteristic):
                            sub._hero = hero

    # NOTE: there is deliberately no per-character template emulation.
    #
    # A character names its template (TEMPLATE="builtIn.Vehicle6E.hdt"), but HD
    # costs it against the template that is actually loaded, and the oracle CLI
    # loads Main6E throughout. The loader used to emulate Vehicle6E for these
    # characters and it was wrong in both halves:
    #
    #   PD/ED costs. Vehicle6E prices them LVLCOST=3 / LVLVAL=2 against Main6E's
    #   1/1. Measured across all 655 fixtures, the oracle uses (1.0, 1.0) for
    #   every character on every template -- Automaton6E 16, Heroic6E 238,
    #   Superheroic6E 300, Vehicle6E 4, no-template 11, not one instance at
    #   (3, 2). Honouring it broke WARLORD - THE FLYING FORTRESS. Retracted
    #   earlier, leaving this function empty of cost overrides.
    #
    #   USESEND. Vehicle6E writes USESEND="No" on the movement powers where
    #   Main6E writes "Yes", and that flag was kept on the grounds that it
    #   "genuinely is No". It genuinely is -- in Vehicle6E, which is not what
    #   the oracle loaded. Forcing it made Charges.parentUsesEND() false on
    #   THE_STARBIRD's Jet Engines, clamping a +0.25 CHARGES away and costing
    #   the Flight 105 against the oracle's 131.
    #
    # Removing the rest of it fixed THE_STARBIRD and moved no other character.
    # If a consumer ever needs true per-character templates, the answer is a
    # TemplateProvider that resolves the named .hdt -- not a hand-rolled patch
    # over Main6E in the loader.

    def _load_powers_section(
        self, root, section_tag: str = "POWERS",
    ) -> list[GenericObject]:
        """
        Load POWERS (or EQUIPMENT) with framework parent-child relationships.

        Two passes:
        1. Build all objects and frameworks, index by ID
        2. Link children to parents via PARENTID

        ``section_tag`` exists because <EQUIPMENT> holds the same element
        shapes as <POWERS> -- 6E2 p182: "Most equipment is built with Powers,
        though Skills are often bought for some types of equipment." A second
        parser would be the same two passes over the same shapes, and would
        drift. The gear-specific attributes (PRICE, WEIGHT, CARRIED, QUANTITY)
        live on the objects, not in the traversal.
        """
        section = root.find(section_tag)
        if section is None:
            return []

        # Pass 1: Build all objects
        objects_by_id: dict[str, GenericObject] = {}
        frameworks: dict[str, GenericObject] = {}
        all_objects: list[tuple[GenericObject, str, str]] = []  # (obj, id, parent_id)

        for elem in section:
            tag = elem.tag
            obj_id = elem.get("ID", "")
            parent_id = elem.get("PARENTID", "")
            xmlid = elem.get("XMLID", tag)

            # Determine if this is a framework
            is_framework = tag in ("LIST", "MULTIPOWER", "VPP", "ELEMENTALCONTROL")

            if is_framework:
                # Instantiate the real framework class (Multipower / VPP /
                # ElementalControl / List) so isinstance() checks in the
                # cost engine work without falling back to xmlid-string
                # matching. The generic LIST tag maps to the real List class
                # so its real_cost_for_child() actually costs the children.
                fw_cls = _FRAMEWORK_CLASSES.get(tag)
                if fw_cls is not None:
                    fw = fw_cls()
                else:
                    fw = _FallbackObject()
                fw._init(elem)
                fw.xmlid = xmlid
                if tag == "MULTIPOWER":
                    fw.xmlid = "MULTIPOWER"
                elif tag == "VPP":
                    fw.xmlid = "VPP"
                elif tag == "ELEMENTALCONTROL":
                    fw.xmlid = "ELEMENTALCONTROL"
                # Store the framework XML tag for round-trip serialization
                fw._framework_tag = tag
                # Load framework modifiers
                for mod_elem in elem.findall("MODIFIER"):
                    mod = self._build_modifier(mod_elem, fw)
                    if mod is not None:
                        fw.assigned_modifiers.append(mod)
                # Load framework adders.
                #
                # A VPP carries its control cost in a CONTROLCOST adder whose
                # LEVELS the file supplies, and VariablePowerPool.__init__
                # synthesises that adder (as Java's init() does) with the rate
                # but no levels. Reading only MODIFIER children left the stub
                # at 0 levels, so every pool in the corpus costed its control
                # at 0 — see tests/test_vpp_control_cost.py.
                #
                # The synthesised adder is UPDATED rather than appended
                # alongside: two CONTROLCOSTs would make control_cost resolve
                # to whichever came first, and Java's getTotalCost adds a
                # non-required adder a second time on top of the explicit
                # CONTROLCOST term.
                for adder_elem in elem.findall("ADDER"):
                    adder = self._build_adder(adder_elem)
                    if adder is None:
                        continue
                    adder_opt = adder_elem.get("OPTIONID", "")
                    if adder_opt:
                        adder.option_id = adder_opt
                    self._apply_template_to_adder(
                        adder, fw.xmlid, adder.xmlid,
                        option_id=adder_opt if adder_opt else None)
                    existing = next(
                        (a for a in fw.assigned_adders
                         if a.xmlid == adder.xmlid), None)
                    if existing is None:
                        fw.assigned_adders.append(adder)
                        continue
                    existing._levels = adder.levels
                    # The stub is the object that survives, so it must also
                    # take over the FILE's identity: kept as-is it wrote back
                    # its own process-local id, and the adder the document
                    # named ceased to exist across a round trip.
                    existing._id = adder._id
                    for provenance in ("_source_tag", "_source_xmlid",
                                       "_source_attrs", "_source_attr_order",
                                       "_source_attr_values",
                                       "_source_child_tags"):
                        if hasattr(adder, provenance):
                            setattr(existing, provenance,
                                    getattr(adder, provenance))
                    # ...and the document's own values, not just its identity:
                    # ALIAS, GRAPHIC, COLOR and the display flags all belong to
                    # the adder the file wrote, while the stub carries whatever
                    # __init__ gave it.
                    existing._alias = adder._alias
                    existing.read_xml_attrs(adder_elem)
                    if adder._base_cost_from_xml:
                        existing.base_cost = adder.base_cost
                    for attr in ("_level_cost", "_level_value"):
                        value = getattr(adder, attr, None)
                        if value:
                            setattr(existing, attr, value)
                if obj_id:
                    frameworks[obj_id] = fw
                # Framework itself is also a power in the list
                all_objects.append((fw, obj_id, parent_id))
            else:
                # Regular power/characteristic
                # Determine obj_type based on tag
                obj_type = "power"
                is_char_in_powers = False
                if tag in ("STR", "DEX", "CON", "BODY", "INT", "EGO", "PRE", "COM",
                           "PD", "ED", "SPD", "REC", "END", "STUN",
                           "OCV", "DCV", "OMCV", "DMCV",
                           "RUNNING", "SWIMMING", "LEAPING", "SIZE"):
                    obj_type = "char"
                    is_char_in_powers = True  # Characteristic in powers section
                elif tag == "SKILL":
                    obj_type = "skill"

                # Java gates the POWERS restore on powerHash/skillHash the same
                # way it gates the other sections (Hero.java:2803, 2818).
                # Characteristics appearing in POWERS are exempt for the same
                # reason as the CHARACTERISTICS section.
                obj = self._build_object(elem, obj_type,
                                         gate_on_template=not is_char_in_powers)
                if obj is not None:
                    # Characteristics in the powers section are power-based
                    if is_char_in_powers and hasattr(obj, '_is_power'):
                        obj._is_power = True
                    if obj_id:
                        objects_by_id[obj_id] = obj
                    all_objects.append((obj, obj_id, parent_id))

        # Pass 2: Link children to frameworks
        for obj, obj_id, parent_id in all_objects:
            if parent_id and parent_id in frameworks:
                fw = frameworks[parent_id]
                obj.parent = fw
                _hold_slot(fw, obj)
                if hasattr(obj, '_is_power'):
                    obj._is_power = True

        # Post-pass: for each Sense, snapshot the group's effective sense
        # adders using only SenseAdder powers that appeared earlier in the
        # list.  This mirrors Java where the SenseGroup cache is populated
        # incrementally during Hero construction: a Detect only "sees"
        # SenseAdder powers that were already loaded (added to the hero's
        # powers list) before it.
        from kirby_cost.objects.powers.sense import Sense
        from kirby_cost.objects.powers.sense_adder import SenseAdder
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.objects.powers.sense_group import SenseGroup

        result = [obj for obj, _, _ in all_objects]
        prior_sense_adders: list[SenseAdder] = []

        for obj in result:
            # Accumulate SenseAdder powers as we go
            if isinstance(obj, SenseAdder):
                prior_sense_adders.append(obj)
            elif isinstance(obj, CompoundPower):
                for sub in getattr(obj, 'powers', []):
                    if isinstance(sub, SenseAdder):
                        prior_sense_adders.append(sub)

            # For Sense/Detect powers, freeze the group adders
            if isinstance(obj, Sense):
                group = obj.group
                if group is not None:
                    frozen = list(group.default_sense_adders)
                    for sa in prior_sense_adders:
                        if group.xmlid in sa.sense_groups and sa.xmlid not in frozen:
                            frozen.append(sa.xmlid)
                    obj._frozen_group_adders = frozen
                else:
                    obj._frozen_group_adders = []

        return result

    def _load_section(self, root, section_tag: str, child_tag: Optional[str],
                      obj_type: str, *,
                      gate_on_template: bool = True) -> list[GenericObject]:
        """Load all objects from an HDC section.

        Also handles PARENTID linking for Enhancer/LIST frameworks in skills
        and perks sections (Scholar, Scientist, Well-Connected, etc.).

        ``gate_on_template`` mirrors Java's per-section hash guard — see the
        note in :meth:`_build_object`.  It is False for CHARACTERISTICS (Java
        restores those positionally from a fixed set) and for MARTIALARTS
        (maneuvers resolve through the template's MANEUVER definitions, not
        through the power/talent hash).
        """
        section = root.find(section_tag)
        if section is None:
            return []

        objects = []
        objects_by_id: dict[str, GenericObject] = {}

        # If child_tag specified, only look for those children
        # Otherwise, load all direct children (POWER, SKILL, etc.)
        if child_tag:
            elements = section.findall(child_tag)
        else:
            elements = list(section)

        # Java builds every section's LIST elements (SKILLS, PERKS, TALENTS,
        # DISADVANTAGES, MARTIALARTS, …) as real com.hero.objects.List instances
        # (Hero.java:2486-2493 and 2640-2646).  A real List has real_cost == 0.0
        # and exposes real_cost_for_child() for parent-linking.  The old
        # _FallbackObject path costed them at 1.0 — a Python bug.  The 655-fixture
        # oracle corpus records "class": "List", "real_cost": 0.0 for all 270
        # GENERIC_OBJECT container entries across every section; never 1.0.
        # Dispatch LIST in every section, not just MARTIALARTS.

        for elem in elements:
            tag = elem.tag
            obj_id = elem.get("ID", "")
            parent_id = elem.get("PARENTID", "")

            # Dispatch LIST elements to the real List class in every section,
            # mirroring Java (Hero.java:2486-2493, 2640-2646).  The XMLID is
            # "GENERIC_OBJECT" which is not registered, so _build_object would
            # produce a _FallbackObject (real_cost 1.0) — wrong for all sections.
            fw_cls = _FRAMEWORK_CLASSES.get(tag)
            if fw_cls is not None:
                obj = fw_cls()
                obj._init(elem)
                xmlid = elem.get("XMLID", tag)
                obj.xmlid = xmlid
                obj._framework_tag = tag
                # Load framework modifiers
                for mod_elem in elem.findall("MODIFIER"):
                    mod = self._build_modifier(mod_elem, obj)
                    if mod is not None:
                        obj.assigned_modifiers.append(mod)
            else:
                obj = self._build_object(elem, obj_type,
                                         gate_on_template=gate_on_template)

            if obj is not None:
                if obj_id:
                    objects_by_id[obj_id] = obj
                objects.append((obj, parent_id))

        # Link children to parents via PARENTID.
        # Link when the parent is a real cost-framework (has real_cost_for_child).
        # The real List class has real_cost_for_child, so maneuvers now link to
        # their style list as Java does (Hero.addManeuver links to the List container).
        #
        # Parents WITHOUT real_cost_for_child (e.g. Enhancer-style Skill objects
        # like SCHOLAR/TRAVELER) remain UNLINKED.  Java models those enhancers as
        # List subclasses; Python hasn't ported Enhancer as a List subclass yet.
        # Skipping them preserves pre-existing behavior and avoids the crash in
        # cost.py:175 (self._parent.real_cost_for_child) that would occur if a
        # child were linked to a plain _FallbackObject or unported Skill parent.
        result = []
        for obj, parent_id in objects:
            if parent_id and parent_id in objects_by_id:
                parent_obj = objects_by_id[parent_id]
                if hasattr(parent_obj, "real_cost_for_child"):
                    obj.parent = parent_obj
                    _hold_slot(parent_obj, obj)
            result.append(obj)

        return result

    def _build_object(self, elem, obj_type: str,
                      parent_list: Optional[GenericObject] = None, *,
                      gate_on_template: bool = False) -> Optional[GenericObject]:
        """Build a GenericObject from an XML element."""
        xmlid = elem.get("XMLID", elem.tag)
        if not xmlid:
            xmlid = elem.tag

        # Java gates every section restore on the template hash and SILENTLY
        # DROPS anything the loaded template doesn't define — the object is
        # never added to the character and contributes no cost:
        #
        #   Hero.java:2609  if (talentHash.get(xmlID) != null) { ... addTalent }
        #   Hero.java:2511  GenericObject skill = skillHash.get(xmlID);
        #                   if (skill != null) { ... addSkill(skill); }
        #   Hero.java:2803  GenericObject p = powerHash.get(xmlID);
        #                   if (p != null) { ... addPower(p); }
        #
        # Python instead fell back to _FallbackObject, which trusts the HDC
        # element's own BASECOST — so a template-undefined object was charged
        # for. The HSEG prefabs carry six <TALENT XMLID="PROGRAM" BASECOST="1">
        # entries; PROGRAM lives in Computer6E.hdt / AI6E.hdt, NOT Main6E.hdt,
        # so Java drops all six while Python billed 6 points (158 vs 152) and
        # shifted every subsequent index in the talents list.
        #
        # Scoped by the caller (see ``_load_section``): characteristics and
        # martial-arts maneuvers resolve through different paths in Java and
        # are not gated here.
        # GENERIC_OBJECT is never a template entry. Java uses it as the XMLID
        # an object falls back to when it has none of its own
        # (GenericObject.getXMLID), so it names app-made containers — the
        # Characteristics and Talents lists a character's powers hang from.
        # Gating it drops the container and orphans its children, which then
        # cost as standalone objects.
        if gate_on_template and xmlid != "GENERIC_OBJECT" \
                and self._get_template_data(xmlid) is None:
            logger.debug(
                "HDC xmlid %r is not defined in the loaded template; dropping "
                "(Java parity: Hero.java section restores skip unknown XMLIDs)",
                xmlid,
            )
            return None

        # The ELEMENT TAG is the authority on what kind of object this is, not
        # the section it happens to sit in. The POWERS section already honours
        # this for its direct children (a <SKILL> or a <STR> under <POWERS>),
        # but a skill NESTED INSIDE a power — Duplication granting Teamwork /
        # Cramming / a KS, a gadget granting Combat Skill Levels — inherited
        # the parent's obj_type="power". _get_power_cls deliberately refuses
        # Skill subclasses, so those fell through to _FallbackObject and lost
        # their real class. 48 objects across ~20 characters, including 26
        # COMBAT_LEVELS in 18 files.
        if obj_type == "power" and elem.tag == "SKILL":
            obj_type = "skill"

        # Create the correct class instance
        obj = self._create_instance(xmlid, obj_type)
        if obj is None:
            return None

        # Initialize from XML
        obj._init(elem)

        # Apply template defaults (the template is the single source of truth)
        option_id = elem.get("OPTIONID", "")
        if option_id:
            obj.option_id = option_id
        self._apply_template_defaults(obj, obj.xmlid, option_id=option_id if option_id else None)

        # Set parent list if in a framework
        if parent_list is not None:
            obj.parent = parent_list
            obj._is_power = True

        # Parse is_power flag
        is_power_str = elem.get("ISPOWER", "")
        if is_power_str.upper().startswith("Y"):
            obj._is_power = True

        # Parse ADD_MODIFIERS_TO_BASE for Characteristics
        add_mod_str = elem.get("ADD_MODIFIERS_TO_BASE", "")
        if add_mod_str.upper().startswith("Y"):
            from kirby_cost.objects.characteristics.characteristic import Characteristic
            if isinstance(obj, Characteristic):
                obj.add_modifiers_to_base = True

        # Parse ultra-slot flag. HDC attribute is ULTRA_SLOT (not ULTRA — that
        # was a typo in the original port). Ultra slots in a Multipower pay
        # active_cost/10; variable slots pay active_cost/5. Default is True
        # (inherited from GenericObject.ultra) — matches HD's default.
        ultra_str = elem.get("ULTRA_SLOT", "")
        if ultra_str.upper().startswith("Y"):
            obj.ultra = True
        elif ultra_str.upper().startswith("N"):
            obj.ultra = False

        # Load modifiers
        for mod_elem in elem.findall("MODIFIER"):
            mod = self._build_modifier(mod_elem, obj)
            if mod is not None:
                obj._assigned_modifiers.append(mod)

        # Load adders and apply template defaults
        for adder_elem in elem.findall("ADDER"):
            adder = self._build_adder(adder_elem)
            if adder is not None:
                adder_opt = adder_elem.get("OPTIONID", "")
                # Persist the adder's chosen option, as the POWER branch does.
                # Java's Adder.getSelectedOption().getXMLID() is exactly this
                # value, and rules such as DangerSense.getAssignedAdders()
                # branch on it. Dropping it made every such check silently
                # false (BOREALIS lost its -5 INTUITIONAL adder).
                if adder_opt:
                    adder.option_id = adder_opt
                self._apply_template_to_adder(adder, obj.xmlid, adder.xmlid,
                                               option_id=adder_opt if adder_opt else None)
                obj._assigned_adders.append(adder)

        # Sense-specific initialization (GROUP, ACTIVE, PROVIDES)
        from kirby_cost.objects.powers.sense import Sense
        if isinstance(obj, Sense):
            group_str = elem.get("GROUP", "")
            if group_str:
                obj.group_id = group_str
            active_str = elem.get("ACTIVE", "")
            if active_str.upper().startswith("Y"):
                obj.active = True
            # HD registers sense groups during template load, so a character
            # with no TEMPLATE has none and nothing can be "provided by the
            # group" — see Sense.total_cost. The same flag already governs a
            # SenseAdder's *GROUP option rate, set below.
            obj.sense_groups_defined = self._character_has_template
            # Parse PROVIDES children (sense adders provided by this sense)
            for provides_elem in elem.findall("PROVIDES"):
                text = (provides_elem.text or "").strip().upper()
                if text and text not in obj.sense_adders:
                    obj.sense_adders.append(text)
            # Apply template PROVIDES (from Main6E.hdt) — these are capabilities
            # built into the sense definition that may not be in the HDC XML.
            for prov in _SENSE_TEMPLATE_PROVIDES.get(obj.xmlid, []):
                if prov not in obj.sense_adders:
                    obj.sense_adders.append(prov)

        # SenseAdder-specific initialization.
        #
        # A sense adder is charged at one of three rates — every sense, a sense
        # group, or a single sense — and the template states all three
        # (ALLCOST / GROUPCOST / SENSECOST). Which one applies depends on what
        # the character bought it for, which the HDC records as the object's
        # OPTIONID. Java resolves it in SenseAdder.setSelectedOption:
        #
        #     if (adder.getXMLID().equals("ALL"))            -> allCost
        #     else if (adder.getXMLID().endsWith("GROUP"))   -> groupCost
        #     else                                           -> senseCost
        #
        # so the selection has to be made for the rate to become a cost.
        # Without it a sense adder costs nothing at all.
        from kirby_cost.objects.powers.sense_adder import SenseAdder
        if isinstance(obj, SenseAdder):
            tmpl = self._get_template_data(obj.xmlid)
            if tmpl is not None:
                if obj.group_cost < 0 and tmpl.group_cost != -1.0:
                    obj.group_cost = tmpl.group_cost
                if obj.sense_cost < 0 and tmpl.sense_cost != -1.0:
                    obj.sense_cost = tmpl.sense_cost
                if obj.all_cost < 0 and tmpl.all_cost != -1.0:
                    obj.all_cost = tmpl.all_cost
            selected = getattr(obj, "option_id", None)
            if selected and obj.selected_option is None:
                from kirby_cost.objects.adder import Adder
                chosen = Adder()
                chosen.xmlid = selected
                # A character that names no template has no sense groups to
                # buy — see _apply_template_defaults, and UNDEAD_GHOUL, which
                # asks for the Smell/Taste Group and is charged for one sense.
                obj.sense_groups_defined = self._character_has_template
                obj.selected_option = chosen

        # Handle List/Framework children (POWER elements inside a LIST)
        if elem.tag in ("LIST", "MULTIPOWER", "VPP", "ELEMENTALCONTROL"):
            # This is a framework — its children are in the powers list
            # They reference this via PARENTID
            pass

        # Handle CompoundPower sub-powers
        # Sub-powers can be <POWER>, <PD>, <ED>, <STR>, or any element type
        from kirby_cost.objects.powers.compound_power import CompoundPower
        if isinstance(obj, CompoundPower):
            for sub_elem in elem:
                if sub_elem.tag in ("NOTES", "MODIFIER", "ADDER"):
                    continue
                # Determine sub-power type
                sub_xmlid = sub_elem.get("XMLID", sub_elem.tag)
                sub_type = "power"
                if sub_elem.tag in ("STR", "DEX", "CON", "BODY", "INT", "EGO", "PRE",
                                     "PD", "ED", "SPD", "REC", "END", "STUN",
                                     "OCV", "DCV", "OMCV", "DMCV",
                                     "RUNNING", "SWIMMING", "LEAPING"):
                    sub_type = "char"
                sub = self._build_object(sub_elem, sub_type, parent_list)
                if sub is not None:
                    if hasattr(sub, '_is_power'):
                        sub._is_power = True
                    obj.powers.append(sub)

        # Handle EnduranceReserve recovery component
        from kirby_cost.objects.powers.endurance_reserve import EnduranceReserve
        if isinstance(obj, EnduranceReserve):
            for sub_elem in elem:
                if sub_elem.tag in ("NOTES", "MODIFIER", "ADDER"):
                    continue
                if sub_elem.get("XMLID", sub_elem.tag) == "ENDURANCERESERVEREC":
                    rec = self._build_object(sub_elem, "power")
                    if rec is not None:
                        obj.rec = rec
                    break

        return obj

    def _create_instance(self, xmlid: str, obj_type: str) -> GenericObject:
        """Create the correct class instance for an XMLID."""
        xmlid_upper = xmlid.upper()

        if obj_type == "char":
            char_map = self._get_char_map()
            cls = char_map.get(xmlid_upper, char_map.get("_DEFAULT"))
            if cls:
                try:
                    return cls(xmlid_upper)
                except TypeError:
                    return cls()
            return _FallbackObject()

        if obj_type == "skill":
            cls = self._get_skill_cls(xmlid_upper)
            if cls:
                try:
                    return cls()
                except (TypeError, AttributeError) as exc:
                    # A class IS registered for this xmlid but failed to
                    # construct — this is a construction bug, not custom
                    # content.  Surface it loudly instead of masking it.
                    self._on_registered_construction_failure(xmlid_upper, cls, exc)
            from kirby_cost.objects.skills.skill import Skill
            return Skill(xmlid_upper)

        if obj_type == "disad":
            from kirby_cost.objects.disads.disadvantage import Disadvantage
            return Disadvantage.get_instance(None) if xmlid_upper in (
                "ENRAGED", "HUNTED", "REPUTATION", "SUSCEPTIBILITY"
            ) else Disadvantage()

        # Powers (and perks, talents, complications) — use registry
        cls = self._get_power_cls(xmlid_upper)
        if cls:
            try:
                return cls()
            except (TypeError, AttributeError) as exc:
                # A class IS registered for this xmlid but failed to
                # construct — surface it loudly instead of silently masking
                # it as a _FallbackObject (which is what hid the construction
                # bugs in the attack / perk / sense classes).
                self._on_registered_construction_failure(xmlid_upper, cls, exc)
        else:
            # No class registered for this xmlid. Two very different cases,
            # and conflating them made this warning cry wolf: it fires
            # thousands of times across the corpus for content that is costed
            # CORRECTLY.
            #
            # If the TEMPLATE defines the xmlid, _FallbackObject picks up its
            # base/level costs and reproduces Java exactly — verified against
            # the oracle: LIGHTSLEEP (64 fixtures), STEALTH (434),
            # COMBAT_LEVELS (348), KNOWLEDGE_SKILL (258) and the rest all sit
            # inside PASSING fixtures. A dedicated class would be nicer for
            # behaviour (a consumer cannot tell a Combat Skill Level from any
            # other object), but it is not a costing defect, and adding one
            # changes cost paths for hundreds of fixtures. Debug, not warning.
            #
            # If the template does NOT define it, the object is genuinely
            # unknown — custom content, or a template mismatch — and that is
            # worth hearing about.
            if self._get_template_data(xmlid_upper) is not None:
                logger.debug(
                    "HDC xmlid %r has no registered class; costed from "
                    "template defaults via _FallbackObject",
                    xmlid_upper,
                )
            else:
                logger.warning(
                    "HDC xmlid %r has no registered class AND no template "
                    "entry; using _FallbackObject",
                    xmlid_upper,
                )
        return _FallbackObject()

    def _on_registered_construction_failure(self, xmlid: str, cls, exc) -> None:
        """Handle a registered class that failed to construct.

        This is always a bug in the engine (the class exists but ``cls()``
        raised), never legitimate custom content.  We never silently swallow
        it: in strict mode we re-raise; otherwise we log at ERROR so it is
        surfaced rather than masked as a _FallbackObject.
        """
        logger.error(
            "Registered class %s for xmlid %r failed to construct: %s: %s",
            getattr(cls, "__name__", cls), xmlid, type(exc).__name__, exc,
        )
        if self._strict:
            raise exc

    def _build_modifier(self, elem, parent: GenericObject) -> Optional[Modifier]:
        """Build a Modifier from an XML element, using specific subclass when available."""
        # Try to get the specific modifier subclass via the factory
        xmlid = elem.get("XMLID", "")
        mod = Modifier.get_instance(elem)
        if mod is None:
            mod = Modifier()
            mod._init(elem)
        mod.parent = parent

        # Apply template defaults for this modifier (costs, options)
        xmlid = elem.get("XMLID", "")
        option_id = elem.get("OPTIONID", "")
        if option_id:
            mod.option_id = option_id
        self._apply_template_to_modifier(mod, xmlid, option_id if option_id else None)

        # Apply power-specific modifier defaults (e.g. INCREASEDSTUNMULTIPLIER
        # is defined inside HKA/RKA in Main6E.hdt, not in the global modifiers section)
        psm = _POWER_SPECIFIC_MODIFIERS.get(xmlid)
        if psm and mod.level_cost == 0.0 and psm.get("level_cost", 0) != 0:
            mod.level_cost = float(psm["level_cost"])
        if psm and mod.level_value == 0.0 and psm.get("level_value", 0) != 0:
            mod.level_value = float(psm["level_value"])
        if psm and mod.base_cost == 0.0 and psm.get("base_cost", 0) != 0:
            mod.base_cost = float(psm["base_cost"])
        if psm:
            if psm.get("min_set"):
                mod.minimum_cost = float(psm["minimum_cost"])
                mod.min_set = True
            if psm.get("max_set"):
                mod.max_cost = float(psm["max_cost"])
                mod.max_set = True

        # Apply modifier types from Main6E.hdt (e.g. VPP type for ZEROPHASE,
        # NOSKILLROLL, HALFPHASE — needed so VPP advantages don't propagate
        # to slot active costs).
        mod_types = _MODIFIER_TYPES.get(xmlid)
        if mod_types:
            for t in mod_types:
                if t not in mod._types:
                    mod._types.append(t)

        # Parse PRIVATE flag
        private_str = elem.get("PRIVATE", "")
        if private_str.upper().startswith("Y"):
            mod.private_mod = True
        elif private_str.upper().startswith("N"):
            mod.private_mod = False

        # Load sub-modifiers (modifiers on modifiers)
        for sub_elem in elem.findall("MODIFIER"):
            sub = self._build_modifier(sub_elem, mod)
            if sub is not None:
                mod.assigned_modifiers.append(sub)

        # Load adders on modifier and apply template defaults
        for adder_elem in elem.findall("ADDER"):
            adder = self._build_adder(adder_elem)
            if adder is not None:
                adder_opt = adder_elem.get("OPTIONID", "")
                # Persist the adder's chosen option, as the POWER branch does.
                # Java's Adder.getSelectedOption().getXMLID() is exactly this
                # value, and rules such as DangerSense.getAssignedAdders()
                # branch on it. Dropping it made every such check silently
                # false (BOREALIS lost its -5 INTUITIONAL adder).
                if adder_opt:
                    adder.option_id = adder_opt
                self._apply_template_to_adder(adder, xmlid, adder.xmlid,
                                               option_id=adder_opt if adder_opt else None)
                mod.assigned_adders.append(adder)

        return mod

    def _build_adder(self, elem) -> Optional[Adder]:
        """Build an Adder from an XML element."""
        adder = Adder()
        adder._init(elem)

        # Parse required/selected flags
        req_str = elem.get("REQUIRED", "")
        if req_str.upper().startswith("Y"):
            adder._required = True

        sel_str = elem.get("SELECTED", "")
        if sel_str.upper().startswith("Y"):
            adder._selected = True
        elif sel_str.upper().startswith("N"):
            adder._selected = False

        # Load nested adders
        for sub_elem in elem.findall("ADDER"):
            sub = self._build_adder(sub_elem)
            if sub is not None:
                adder.assigned_adders.append(sub)

        # Apply types from HDT template (e.g. RIDING, DRIVING, PILOTING
        # on TF sub-adders — needed for discount calculations)
        self._apply_adder_types(adder)

        return adder
