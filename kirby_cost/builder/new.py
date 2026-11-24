"""A new, empty build on any template.

The builder's third layer (two-databases spec §4a). An AI building an NPC,
a base or a vehicle (Peter, 2026-11-24) starts from nothing on the right
template; `buy` and `apply` then add to it. The new build holds exactly what
HD gives a new character on that template: its characteristics (the
template's own, after REMOVEs, in HD's order: `HDTTemplateProvider.
characteristics()`), every one at 0 levels, and empty sections. It costs 0.

NO DEFAULTS: the template, name and the three point totals are all
required.
"""
from __future__ import annotations

from enum import Enum

from kirby_cost.builder.edits import Node

#: The sections an HD character file carries, in HD's order.
_SECTIONS = ("BASIC_CONFIGURATION", "CHARACTER_INFO", "CHARACTERISTICS",
             "SKILLS", "PERKS", "TALENTS", "MARTIALARTS", "POWERS",
             "DISADVANTAGES", "EQUIPMENT")


class Template(Enum):
    """The 6E templates HD ships, by the name a character file declares."""

    MAIN = "builtIn.Main6E.hdt"
    SUPERHEROIC = "builtIn.Superheroic6E.hdt"
    HEROIC = "builtIn.Heroic6E.hdt"
    BASE = "builtIn.Base6E.hdt"
    VEHICLE = "builtIn.Vehicle6E.hdt"
    AUTOMATON = "builtIn.Automaton6E.hdt"
    COMPUTER = "builtIn.Computer6E.hdt"
    AI = "builtIn.AI6E.hdt"


def new_build(template: Template, *, template_provider, name: str,
              base_points: int, disad_points: int, experience: int) -> dict:
    """A build doc for a new character on ``template``, costed against the
    template files ``template_provider`` reads (an `HDTTemplateProvider`)."""
    chain = template_provider.for_template(template.value)
    characteristics: list[Node] = [
        {"tag": xmlid,
         "attrs": {"XMLID": xmlid, "ID": str(n), "LEVELS": "0",
                   "POSITION": str(n)},
         "children": []}
        for n, xmlid in enumerate(chain.characteristics(), start=1)
    ]
    attrs = {
        "BASIC_CONFIGURATION": {"BASE_POINTS": str(base_points),
                                "DISAD_POINTS": str(disad_points),
                                "EXPERIENCE": str(experience),
                                "RULES": "Default"},
        "CHARACTER_INFO": {"CHARACTER_NAME": name},
    }
    sections = [{"tag": tag, "attrs": attrs.get(tag, {}),
                 "children": characteristics if tag == "CHARACTERISTICS" else []}
                for tag in _SECTIONS]
    return {"document": {"tag": "CHARACTER",
                         "attrs": {"version": "6.0", "TEMPLATE": template.value},
                         "children": sections},
            "encoding": "utf-16"}


__all__ = ["Template", "new_build"]
