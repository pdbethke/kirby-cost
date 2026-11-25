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

from kirby_cost.io.build_json import Section


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
    """A curated build doc for a new character on ``template``, costed
    against the template files ``template_provider`` reads (an
    `HDTTemplateProvider`)."""
    chain = template_provider.for_template(template.value)
    doc: dict = {"name": name, "template": template.value,
                 "base_points": base_points, "disad_points": disad_points,
                 "experience": experience}
    for section in Section:
        doc[section.key] = []
    doc[Section.CHARACTERISTICS.key] = [
        {"id": str(n), "xmlid": xmlid, "levels": 0}
        for n, xmlid in enumerate(chain.characteristics(), start=1)
    ]
    return doc


__all__ = ["Template", "new_build"]
