"""A template's <REMOVE> takes an inherited entry away (HD's Template.java).

Found 2026-11-24 building a new vehicle through the builder: the provider
walks a template's `extends` chain (Vehicle6E over Main6E) and skipped every
<REMOVE> element, so a Vehicle6E build was offered CON, INT, EGO, PRE, OMCV,
DMCV, REC, END and STUN, which Vehicle6E removes. Worse, in CHARACTERISTICS
and POWERS the parser read <REMOVE> as an ENTRY, so "REMOVE" was a
characteristic of every template that used one.

HD's rule (Template.java, each section): while a template loads, every
<REMOVE>id</REMOVE> deletes ``id`` from what that section inherited, then
the template's own entries are added. The provider loads child-first, so it
skips, in each ancestor, what a descendant removed from that section.
"""
from __future__ import annotations

import pytest

from kirby_cost.template.hdt_provider import HDTTemplateProvider

VEHICLE_REMOVES = ("CON", "INT", "EGO", "PRE", "OMCV", "DMCV", "REC", "END", "STUN")


@pytest.fixture(scope="module")
def main():
    return HDTTemplateProvider()


@pytest.fixture(scope="module")
def vehicle(main):
    return main.for_template("builtIn.Vehicle6E.hdt")


@pytest.mark.parametrize("xmlid", VEHICLE_REMOVES)
def test_a_vehicle_has_no_characteristic_its_template_removes(vehicle, main, xmlid):
    assert main.get_template_data(xmlid, "characteristics") is not None
    assert (xmlid, "characteristics") not in {
        (x, s) for (s, x) in vehicle._by_section}


def test_a_vehicle_keeps_what_it_does_not_remove(vehicle):
    kept = {x for (s, x) in vehicle._by_section if s == "characteristics"}
    assert {"STR", "DEX", "BODY", "SIZE", "SPD"} <= kept


def test_a_removed_skill_is_gone_too(vehicle, main):
    assert main.get_template_data("JACK_OF_ALL_TRADES", "skills") is not None
    assert ("skills", "JACK_OF_ALL_TRADES") not in vehicle._by_section


@pytest.mark.parametrize("template", [
    "builtIn.Main6E.hdt", "builtIn.Vehicle6E.hdt", "builtIn.Base6E.hdt",
    "builtIn.Superheroic6E.hdt", "builtIn.Automaton6E.hdt",
])
def test_remove_is_never_an_entry(main, template):
    provider = main.for_template(template)
    assert not any(x == "REMOVE" for (_s, x) in provider._by_section)
