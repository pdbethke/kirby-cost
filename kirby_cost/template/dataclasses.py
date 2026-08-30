"""Frozen dataclasses modelling HERO System template definitions.

These represent the shape of data the cost engine expects from any source
(HDT JSON, database, or test fixtures).  They are source-agnostic — the
loader converts raw dicts into these before handing them to domain objects.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class OptionTemplate:
    """A selectable option within a power or adder (e.g. Energy / Physical)."""

    xmlid: str
    display: str = ""
    #: What HD PRINTS for this option, which is not always what it CALLS it.
    #: `<OPTION XMLID="HALFEND" DISPLAY="Half END" ALIAS="1/2 END">` names
    #: itself twice and the sheet shows the second one. Java stores an option
    #: as an Adder and reads `getAlias()`, which falls back to display only
    #: when no alias was given (GenericObject.java:1238).
    alias: str = ""
    #: Whether HD prints this option at all. AVAD's twenty options are the
    #: reason: they name the frequency shift that PRICES the modifier
    #: ("Very Common -> Rare") and every one of them is DISPLAYINSTRING="No",
    #: because the sheet shows the DEFENCE, not the arithmetic behind the cost.
    display_in_string: bool = True
    #: The option's own LEVELS, which the template writes as LEVELSTART.
    #: Autofire reads it to say how many shots: `<OPTION XMLID="THREE"
    #: DISPLAY="3 Shots" LEVELSTART="3">` is the only place the number 3
    #: exists as a number rather than as text.
    levels: int = 0
    base_cost: float = 0.0
    level_cost: float = 0.0
    level_value: float = 0.0
    level_power: int = 1
    level_multiplier: int = 1


@dataclass(frozen=True)
class AdderTemplate:
    """Template for a purchasable adder (e.g. +1/2 d6, Riding Animals)."""

    xmlid: str
    display: str = ""
    #: What HD prints for this adder, which is not always its DISPLAY.
    #: Reputation's EXTREME is `DISPLAY="Extreme" ALIAS="(Extreme"` — the
    #: unclosed bracket is deliberate, and the renderer's paren counting
    #: exists to close it at the end of the line.
    alias: str = ""
    #: Whether this adder offers sub-adders of its own. Java asks
    #: `getAvailableAdders().size() > 0` to decide whether an adder is a GROUP,
    #: and group adders print BEFORE the plain ones — which is why HD writes
    #: "Common Melee Weapons, Bows, Lances" and not the flat alphabetical
    #: "Bows, Common Melee Weapons, Lances".
    has_sub_adders: bool = False
    #: Whether the template REQUIRES this adder. HDC files never say so — it
    #: is a property of the template, not of the character — and the display
    #: layer branches on it: a required adder prints only its option, an
    #: optional one prints its own name too.
    required: bool = False
    base_cost: float = 0.0
    level_cost: float = 0.0
    level_value: float = 0.0
    level_power: int = 1
    level_multiplier: int = 1
    types: tuple[str, ...] = ()
    #: The adder's own selectable options, by xmlid. The .hdt parser has
    #: always read these (hdt_parser._parse_options) but the provider dropped
    #: them, so an adder's chosen option had no template to be restored from
    #: and the loader had to fall back to the DOCUMENT's alias for its
    #: display. Those are different strings on purpose -- Main6E declares
    #: `<OPTION XMLID="VERYCOMMON" DISPLAY="Very Common" ALIAS="(Very Common">`
    #: -- and an export printed the bracketed one where HD prints the label.
    options: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TemplateData:
    """Full template for a power, skill, modifier, or other purchasable object."""

    xmlid: str
    display: str = ""
    base_cost: float = 0.0
    level_cost: float = 0.0
    level_value: float = 0.0
    level_power: int = 1
    level_multiplier: int = 1
    minimum_cost: float = 0.0
    min_set: bool = False
    max_cost: float = 0.0
    max_set: bool = False
    duration: str = ""
    #: "Yes", "Self", "LOS", "No" — a WORD, not a distance. getRangeValue
    #: derives the metres from the cost; this says whether the power is ranged
    #: at all, and it is stated only by the template.
    range: str = ""
    target: str = ""
    #: Which defence the power is tested against -- NORMAL, MENTAL, POWER,
    #: SPECIAL, NONE. `hdt_parser` has always read it (:333) and nothing
    #: carried it, so every loaded power reported the constructor's "NONE"
    #: and a consumer had to guess. kirby-combat guessed by xmlid and said so:
    #: "without a reliable signal in kirby-cost's parse we default to PD for
    #: HKA/HTH and ED for ranged blasts".
    defense: str = ""
    #: Combat facts the template states about the power itself. TRI-STATE:
    #: ``None`` means "the template said nothing", which is NOT the same as
    #: ``False`` -- a class such as KillingAttackRanged sets ``killing = True``
    #: in its constructor, and a template that is silent must not undo that.
    #: An explicit ``KILLING="No"`` in the .hdt DOES undo it, which is the
    #: point: a GM running a heroic campaign edits the template, kirby-cost
    #: emits the changed fact, and kirby-combat acts on it. Same for the rest.
    killing: Optional[bool] = None
    does_body: Optional[bool] = None
    does_damage: Optional[bool] = None
    does_knockback: Optional[bool] = None
    #: Field names this campaign forced, set by the provider when a
    #: CampaignRules is active. `apply_template` reads it to let a campaign
    #: outrank a value the character's own .hdc stated -- a house rule a
    #: character can be exempt from is not a rule.
    campaign_forced: frozenset = frozenset()
    uses_end: bool = False
    is_power: bool = False
    class_name: str = ""
    # Starting/base value for characteristic-category templates (HDT
    # ``BASE="10"`` on ``<STR>``, ``BASE="2"`` on ``<SPD>`` etc.). 0.0
    # for non-characteristic templates (powers, skills, modifiers).
    base_value: float = 0.0
    # Sense rates, straight off the element (``ALLCOST`` / ``GROUPCOST`` /
    # ``SENSECOST``). HD charges a sense adder at one of three rates depending
    # on whether it was bought for every sense, a sense group, or one sense —
    # ``SenseAdder.selected_option`` picks between them. ``-1.0`` is the
    # engine's established "not applicable" marker, so an element that names no
    # rate keeps that meaning.
    all_cost: float = -1.0
    group_cost: float = -1.0
    sense_cost: float = -1.0
    adders: dict[str, AdderTemplate] = field(default_factory=dict)
    options: dict[str, OptionTemplate] = field(default_factory=dict)
    option_aliases: dict[str, str] = field(default_factory=dict)
    types: tuple[str, ...] = ()
    #: Applicability, as the template states it. HD's Modifier.included()
    #: refuses a modifier when the power, or any modifier already on it, is
    #: one of ``excludes``; and requires one of ``requires`` (all of them when
    #: ``requires_all``). Both are <EXCLUDES>/<REQUIRES> text children --
    #: parsed for years, dropped by the provider until 2026-08-29.
    excludes: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    requires_all: bool = False
    # The element's raw attributes, for the detail no named field carries. A
    # maneuver is mostly detail — OCV, DCV, PHASE, DC, KILLING, EFFECT — and
    # Java hands the whole Maneuver object to whoever asks, so a consumer that
    # wants to describe Killing Strike rather than just price it needs them.
    attributes: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory: build from the raw JSON dict produced by hd6cli --dump-template
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, xmlid: str, raw: dict) -> "TemplateData":
        """Create a TemplateData from a raw template JSON entry."""
        options = {
            oid: OptionTemplate(
                xmlid=oid,
                display=oval.get("display", ""),
                base_cost=float(oval.get("base_cost", 0)),
                level_cost=float(oval.get("level_cost", 0)),
                level_value=float(oval.get("level_value", 0)),
                level_power=int(oval.get("level_power", 1)),
                level_multiplier=int(oval.get("level_multiplier", 1)),
            )
            for oid, oval in raw.get("options", {}).items()
        }
        adders = {
            aid: AdderTemplate(
                xmlid=aid,
                display=aval.get("display", ""),
                base_cost=float(aval.get("base_cost", 0)),
                level_cost=float(aval.get("level_cost", 0)),
                level_value=float(aval.get("level_value", 0)),
                level_power=int(aval.get("level_power", 1)),
                level_multiplier=int(aval.get("level_multiplier", 1)),
                types=tuple(aval.get("types", [])),
            )
            for aid, aval in raw.get("adders", {}).items()
        }
        return cls(
            xmlid=xmlid,
            display=raw.get("display", ""),
            base_cost=float(raw.get("base_cost", 0)),
            level_cost=float(raw.get("level_cost", 0)),
            level_value=float(raw.get("level_value", 0)),
            level_power=int(raw.get("level_power", 1)),
            level_multiplier=int(raw.get("level_multiplier", 1)),
            minimum_cost=float(raw.get("minimum_cost", 0)),
            min_set=bool(raw.get("min_set", False)),
            max_cost=float(raw.get("max_cost", 0)),
            max_set=bool(raw.get("max_set", False)),
            duration=raw.get("duration", ""),
            target=raw.get("target", ""),
            uses_end=bool(raw.get("uses_end", False)),
            is_power=bool(raw.get("is_power", False)),
            class_name=raw.get("class", ""),
            base_value=float(raw.get("base_value", 0)),
            all_cost=float(raw.get("all_cost", -1)),
            group_cost=float(raw.get("group_cost", -1)),
            sense_cost=float(raw.get("sense_cost", -1)),
            adders=adders,
            options=options,
            option_aliases=dict(raw.get("option_aliases", {})),
            types=tuple(raw.get("types", [])),
        )
