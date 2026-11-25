"""A purchase named by XMLID, made into a build element from the template.

The builder's second layer (two-databases spec §4a). An AI building an NPC,
a base or equipment (Peter, 2026-11-24) names what it wants — "Energy
Blast, 8 levels, 0 END" — and never writes a build doc by hand. The
purchase made here (a curated build-doc object, see `edits`)
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

from kirby_cost.builder.edits import Add, EditConflict, Obj, ids
from kirby_cost.io.build_json import Section


class NotInTemplate(EditConflict):
    """A purchase names something the template does not define."""


class Kind(Enum):
    """What a purchase is: where the template defines it, and the build
    section it goes in."""

    POWER = ("powers", Section.POWERS)
    EQUIPMENT = ("powers", Section.EQUIPMENT)
    SKILL = ("skills", Section.SKILLS)
    PERK = ("perks", Section.PERKS)
    TALENT = ("talents", Section.TALENTS)
    COMPLICATION = ("disadvantages", Section.COMPLICATIONS)

    @property
    def template_section(self) -> str:
        return self.value[0]

    @property
    def build_section(self) -> Section:
        return self.value[1]


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
        numeric = [int(i) for i in ids(doc) if str(i).isdigit()]
        self._next = (max(numeric) if numeric else 0) + 1

    def __call__(self) -> str:
        out, self._next = str(self._next), self._next + 1
        return out


def _option(owner: str, what: str, option: str | None,
            options: Any) -> dict[str, str]:
    if option is None:
        return {}
    if option not in (options or {}):
        raise NotInTemplate(
            f"{owner}: the template has no option {option!r} for {what} "
            f"(it has {sorted(options or {})})")
    return {"option_id": option}


def _pick(owner: str, pick: Pick, entry: Any) -> Obj:
    return {"xmlid": pick.xmlid, "levels": pick.levels,
            **_option(owner, pick.xmlid, pick.option,
                      getattr(entry, "options", None))}


def element(purchase: Purchase, *, template, mint) -> Obj:
    """The build element for ``purchase``, every name checked against
    ``template`` (a `TemplateProvider`)."""
    kind = purchase.kind
    entry = template.get_template_data(purchase.xmlid, kind.template_section)
    if entry is None or entry.xmlid != purchase.xmlid:
        raise NotInTemplate(
            f"{purchase.xmlid}: not a {kind.template_section[:-1]} in the template")
    obj: Obj = {"id": mint(), "xmlid": purchase.xmlid,
                "levels": purchase.levels, "name": purchase.name,
                **_option(purchase.xmlid, purchase.xmlid, purchase.option,
                          entry.options)}
    if kind is Kind.SKILL:
        # The doc's own marker (`Skill.to_build_dict`): the rebuild writes a
        # SKILL element, so the loader dispatches through the skill registry.
        obj["skill"] = True
    adders: list[Obj] = []
    for pick in purchase.adders:
        offered = entry.adders or {}
        if pick.xmlid not in offered:
            raise NotInTemplate(
                f"{purchase.xmlid}: the template gives it no adder {pick.xmlid!r}")
        adder = _pick(purchase.xmlid, pick, offered[pick.xmlid])
        # A template adder is a CHOICE in HD, counted only when selected
        # (every HD-saved adder states SELECTED="YES"). Stating it is the
        # purchase's choice, not a cost.
        adder["selected"] = True
        adders.append(adder)
    modifiers: list[Obj] = []
    for pick in purchase.modifiers:
        mod = template.get_template_data(pick.xmlid, "modifiers")
        if mod is None or mod.xmlid != pick.xmlid:
            raise NotInTemplate(f"{pick.xmlid}: not a modifier in the template")
        modifiers.append(_pick(purchase.xmlid, pick, mod))
    if adders:
        obj["adders"] = adders
    if modifiers:
        obj["modifiers"] = modifiers
    return obj


def buy(doc: dict, purchase: Purchase, *, template) -> Add:
    """The `Add` edit that buys ``purchase`` into ``doc``'s build, with an ID
    new to it. Apply it with `apply` (alone or among other edits)."""
    return Add(purchase.kind.build_section,
               element(purchase, template=template, mint=_IdMint(doc)))


__all__ = ["Kind", "NotInTemplate", "Pick", "Purchase", "buy", "element"]
