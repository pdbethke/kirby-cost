"""A purchase named by XMLID, made into a build element from the template.

The builder's second layer (two-databases spec §4a). An AI building an NPC,
a base or equipment (Peter, 2026-11-24) names what it wants — "Energy
Blast, 8 levels, 0 END" — and never writes HD's XML. The element made here
states only what the purchase CHOSE: XMLID, levels, name, option, and its
adders and modifiers. Every cost is left to the template, which the loader
merges in exactly as it does for an HD-saved file (HDC stores only
overrides). So there is no cost number here to drift from the engine.

NAMED OR REFUSED. Every XMLID and option must exist in the template the
build is costed against, or the purchase is refused by name
(`NotInTemplate`). Whether a modifier is LEGAL on this power is the
validation layer's question (`kirby_cost.validation`), asked of the costed
build, not this one's.

NO DEFAULTS. Every `Purchase` and `Pick` field is required: a purchase with
no option says ``option=None``, one with no modifiers says
``modifiers=()``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from kirby_cost.builder.edits import Add, EditConflict, Node, _ids


class NotInTemplate(EditConflict):
    """A purchase names something the template does not define."""


class Kind(Enum):
    """Where a purchase goes: its template section, build section and tag."""

    POWER = ("powers", "POWERS", "POWER")
    EQUIPMENT = ("powers", "EQUIPMENT", "POWER")
    SKILL = ("skills", "SKILLS", "SKILL")
    PERK = ("perks", "PERKS", "PERK")
    TALENT = ("talents", "TALENTS", "TALENT")
    COMPLICATION = ("disadvantages", "DISADVANTAGES", "DISAD")

    @property
    def template_section(self) -> str:
        return self.value[0]

    @property
    def build_section(self) -> str:
        return self.value[1]

    @property
    def tag(self) -> str:
        return self.value[2]


@dataclass(frozen=True)
class Pick:
    """An adder or modifier on a purchase: its XMLID, levels and option."""

    xmlid: str
    levels: int
    option: str | None


@dataclass(frozen=True)
class Purchase:
    """One thing bought, by XMLID."""

    kind: Kind
    xmlid: str
    levels: int
    name: str
    option: str | None
    adders: tuple[Pick, ...]
    modifiers: tuple[Pick, ...]


class _IdMint:
    """New HD IDs for one build: above every numeric ID it holds, so they
    cannot collide and are the same on every run (HD's own are millisecond
    timestamps, numeric)."""

    def __init__(self, doc: dict) -> None:
        numeric = [int(i) for i in _ids(doc["document"]) if str(i).isdigit()]
        self._next = (max(numeric) if numeric else 0) + 1

    def __call__(self) -> str:
        out, self._next = str(self._next), self._next + 1
        return out


def _option_attrs(owner: str, what: str, option: str | None,
                  options: Any) -> dict[str, str]:
    if option is None:
        return {}
    if option not in (options or {}):
        raise NotInTemplate(
            f"{owner}: the template has no option {option!r} for {what} "
            f"(it has {sorted(options or {})})")
    return {"OPTION": option, "OPTIONID": option}


def _pick_node(owner: str, tag: str, pick: Pick, entry: Any, mint) -> Node:
    attrs = {"XMLID": pick.xmlid, "ID": mint(), "LEVELS": str(pick.levels),
             **_option_attrs(owner, pick.xmlid, pick.option,
                             getattr(entry, "options", None))}
    return {"tag": tag, "attrs": attrs, "children": []}


def element(purchase: Purchase, *, template, mint, position: int) -> Node:
    """The build element for ``purchase``, every name checked against
    ``template`` (a `TemplateProvider`)."""
    kind = purchase.kind
    entry = template.get_template_data(purchase.xmlid, kind.template_section)
    if entry is None or entry.xmlid != purchase.xmlid:
        raise NotInTemplate(
            f"{purchase.xmlid}: not a {kind.template_section[:-1]} in the template")
    attrs = {"XMLID": purchase.xmlid, "ID": mint(),
             "LEVELS": str(purchase.levels), "NAME": purchase.name,
             "POSITION": str(position),
             **_option_attrs(purchase.xmlid, purchase.xmlid, purchase.option,
                             entry.options)}
    children: list[Node] = []
    for pick in purchase.adders:
        adders = entry.adders or {}
        if pick.xmlid not in adders:
            raise NotInTemplate(
                f"{purchase.xmlid}: the template gives it no adder {pick.xmlid!r}")
        node = _pick_node(purchase.xmlid, "ADDER", pick, adders[pick.xmlid], mint)
        # A template adder is a CHOICE in HD, counted only when selected
        # (every HD-saved adder states SELECTED="YES"). Stating it is the
        # purchase's choice, not a cost.
        node["attrs"]["SELECTED"] = "YES"
        children.append(node)
    for pick in purchase.modifiers:
        mod = template.get_template_data(pick.xmlid, "modifiers")
        if mod is None or mod.xmlid != pick.xmlid:
            raise NotInTemplate(f"{pick.xmlid}: not a modifier in the template")
        children.append(_pick_node(purchase.xmlid, "MODIFIER", pick, mod, mint))
    return {"tag": kind.tag, "attrs": attrs, "children": children}


def buy(doc: dict, purchase: Purchase, *, template) -> Add:
    """The `Add` edit that buys ``purchase`` into ``doc``'s build, with IDs
    new to it. Apply it with `apply` (alone or among other edits)."""
    section = next((c for c in doc["document"].get("children", [])
                    if c.get("tag") == purchase.kind.build_section), None)
    position = len(section.get("children", [])) if section is not None else 0
    node = element(purchase, template=template, mint=_IdMint(doc),
                   position=position)
    return Add(purchase.kind.build_section, node)


__all__ = ["Kind", "NotInTemplate", "Pick", "Purchase", "buy", "element"]
