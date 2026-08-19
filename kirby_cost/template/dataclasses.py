"""Frozen dataclasses modelling HERO System template definitions.

These represent the shape of data the cost engine expects from any source
(HDT JSON, database, or test fixtures).  They are source-agnostic — the
loader converts raw dicts into these before handing them to domain objects.
"""
from dataclasses import dataclass, field


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
    base_cost: float = 0.0
    level_cost: float = 0.0
    level_value: float = 0.0
    level_power: int = 1
    level_multiplier: int = 1
    types: tuple[str, ...] = ()


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
    target: str = ""
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
