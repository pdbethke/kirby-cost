"""The builder's second layer: a purchase named by XMLID, filled from the template.

An AI building an NPC, a base or a piece of equipment (Peter, 2026-11-24)
asks for "Energy Blast, 8 levels, 0 END" and never writes HD's XML: the
builder makes the element, stating only what the purchase chose (XMLID,
levels, name, option, its adders and modifiers), and the loader fills every
cost from the character's template exactly as it does for an HD-saved file.

Everything named must exist in the template, or the purchase is refused by
name (`NotInTemplate`). Whether a modifier is LEGAL on the power is the
engine's validation layer's question, not this one's.
"""
from __future__ import annotations

import pytest

from kirby_cost.builder import (
    Kind, NotInTemplate, Pick, Purchase, apply, buy,
)
from kirby_cost.io.formats import load_build
from kirby_cost.template.hdt_provider import HDTTemplateProvider
from tests.corpus import require_authored_hdc


@pytest.fixture(scope="module")
def template():
    return HDTTemplateProvider()


@pytest.fixture(scope="module")
def ravel():
    return load_build(str(require_authored_hdc("Ravel")), format="hdc").export(format="json")


def _blast(**over):
    fields = dict(kind=Kind.POWER, xmlid="ENERGYBLAST", levels=8,
                  name="Test Blast", option=None, adders=(), modifiers=())
    fields.update(over)
    return Purchase(**fields)


def _bought(doc, purchase, template):
    edit = buy(doc, purchase, template=template)
    out = apply(doc, [edit])
    hero = load_build(out, format="json")
    new_id = edit.node["attrs"]["ID"]
    every = (list(hero.powers) + list(hero.skills) + list(hero.perks)
             + list(hero.talents) + list(hero.equipment) + list(hero.complications))
    (obj,) = [o for o in every if str(o.id) == new_id]
    return out, obj


def test_a_power_by_xmlid_costs_what_the_template_says(ravel, template):
    _, blast = _bought(ravel, _blast(), template)
    assert blast.active_cost == 40              # 5 points a die (6E1 p.193)


def test_a_modifier_with_an_option(ravel, template):
    zero_end = _blast(modifiers=(Pick(xmlid="REDUCEDEND", levels=0, option="ZERO"),))
    _, blast = _bought(ravel, zero_end, template)
    assert blast.active_cost == 60              # 0 END is +1/2 (6E1 p.346)


def test_an_adder(ravel, template):
    half = _blast(adders=(Pick(xmlid="PLUSONEHALFDIE", levels=0, option=None),))
    _, blast = _bought(ravel, half, template)
    assert blast.active_cost == 43              # +1/2d6 is 3 points


def test_a_skill(ravel, template):
    out, _ = _bought(ravel, Purchase(kind=Kind.SKILL, xmlid="CONCEALMENT", levels=0,
                                     name="", option=None, adders=(), modifiers=()),
                     template)
    assert load_build(out, format="json").total_points > load_build(ravel, format="json").total_points


def test_new_ids_are_new(ravel, template):
    one = buy(ravel, _blast(modifiers=(Pick("REDUCEDEND", 0, "ZERO"),)), template=template)
    ids = [n["attrs"]["ID"] for n in [one.node, *one.node["children"]]]
    assert len(set(ids)) == len(ids)
    apply(ravel, [one])                         # no ID collides with the build


def test_an_unknown_power_is_refused(ravel, template):
    with pytest.raises(NotInTemplate, match="NOSUCHPOWER"):
        buy(ravel, _blast(xmlid="NOSUCHPOWER"), template=template)


def test_an_unknown_option_is_refused(ravel, template):
    with pytest.raises(NotInTemplate, match="FREE"):
        buy(ravel, _blast(modifiers=(Pick("REDUCEDEND", 0, "FREE"),)), template=template)


def test_an_unknown_modifier_is_refused(ravel, template):
    with pytest.raises(NotInTemplate, match="NOSUCHMOD"):
        buy(ravel, _blast(modifiers=(Pick("NOSUCHMOD", 0, None),)), template=template)


def test_an_adder_the_power_does_not_have_is_refused(ravel, template):
    with pytest.raises(NotInTemplate, match="TROPICAL"):
        buy(ravel, _blast(adders=(Pick("TROPICAL", 0, None),)), template=template)


def test_equipment_goes_in_the_equipment_section(ravel, template):
    edit = buy(ravel, _blast(kind=Kind.EQUIPMENT), template=template)
    assert edit.section == "EQUIPMENT" and edit.node["tag"] == "POWER"
