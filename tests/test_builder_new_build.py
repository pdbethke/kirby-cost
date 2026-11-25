"""The builder's third layer: a new, empty build on any template.

An AI building an NPC, a base or a vehicle (Peter, 2026-11-24) starts from
nothing on the right template. HD gives a new character the characteristics
its template chain defines, after REMOVEs, in the template's POSITION order:
never the earlier-edition fallback's (Main.hdt's COM, Vehicle.hdt's DEF).

The expected lists below are HD's own answer: each new build was written to
.hdc and dumped by the headless oracle (kirby-hd-oracle hd6cli.sh,
2026-11-24), which lists `hero.getCharacteristics()`.
"""
from __future__ import annotations

import pytest

from kirby_cost.builder import Template, new_build
from kirby_cost.io.build_json import build_from_json
from kirby_cost.template.hdt_provider import HDTTemplateProvider

MAIN = ["STR", "DEX", "CON", "INT", "EGO", "PRE", "OCV", "DCV", "OMCV", "DMCV",
        "SPD", "PD", "ED", "REC", "END", "BODY", "STUN", "RUNNING", "SWIMMING",
        "LEAPING"]

HD_SAYS = {
    Template.SUPERHEROIC: MAIN,
    Template.HEROIC: MAIN,
    Template.AUTOMATON: MAIN,
    Template.BASE: ["BASESIZE", "PD", "ED", "BODY"],
    Template.VEHICLE: ["SIZE", "STR", "DEX", "BODY", "SPD", "OCV", "DCV", "PD",
                       "ED", "RUNNING", "SWIMMING", "LEAPING"],
    Template.COMPUTER: ["DEX", "INT", "OCV", "DCV", "OMCV", "DMCV", "SPD"],
    Template.AI: ["DEX", "INT", "EGO", "OCV", "DCV", "OMCV", "DMCV", "SPD"],
}


@pytest.fixture(scope="module")
def provider():
    return HDTTemplateProvider()


def _new(template, provider, **over):
    fields = dict(name="Nobody", base_points=400, disad_points=75,
                  experience=0)
    fields.update(over)
    return new_build(template, template_provider=provider, **fields)


@pytest.mark.parametrize("template", list(HD_SAYS))
def test_a_new_build_has_what_hd_gives_its_template(template, provider):
    hero = build_from_json(_new(template, provider))
    assert [c.xmlid for c in hero.characteristics] == HD_SAYS[template]


@pytest.mark.parametrize("template", list(HD_SAYS))
def test_a_new_build_costs_nothing(template, provider):
    assert build_from_json(_new(template, provider)).total_points == 0


def test_a_new_build_declares_its_template_and_its_points(provider):
    doc = _new(Template.VEHICLE, provider, name="The Ramblin' Wreck",
               base_points=200, disad_points=0, experience=5)
    hero = build_from_json(doc)
    assert hero.template_name == "builtIn.Vehicle6E.hdt"
    assert (hero.name, hero.base_points, hero.disad_points, hero.experience) == (
        "The Ramblin' Wreck", 200, 0, 5)
