"""A campaign's .hdt states combat facts, and the engine emits them.

This is the seam that makes house rules possible. A GM who wants killing
attacks to behave as normal damage in a heroic campaign, or who wants to turn
knockback off, edits the template -- and every consumer downstream sees the
changed fact without anyone editing code. kirby-cost is the only thing that
reads the .hdt, so kirby-cost is where those facts have to enter the model.

Before 2026-08-25 they did not enter it at all: `KillingAttackRanged.__init__`
hardcoded `self.killing = True` and the template's `KILLING="Yes"` was read by
`hdt_parser` and dropped. Editing the .hdt changed nothing.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from kirby_cost.io.hdt_parser import HDTParser
from kirby_cost.template.dataclasses import TemplateData
from kirby_cost.objects.powers.killing_attack_ranged import KillingAttackRanged


def _parse(tag_text: str) -> dict:
    return HDTParser()._parse_generic_object(ET.fromstring(tag_text))


def test_the_parser_reads_killing_from_the_template():
    entry = _parse('<RKA KILLING="Yes" DEFENSE="NORMAL"/>')

    assert entry["killing"] is True


def test_a_template_that_says_no_is_not_the_same_as_a_template_that_is_silent():
    """The tri-state is load-bearing. `KillingAttackRanged` sets killing in
    its own constructor, so "absent" must not read as "No" -- otherwise
    applying any template at all would quietly disarm every killing attack."""
    assert _parse('<RKA KILLING="No"/>')["killing"] is False
    assert _parse('<RKA/>')["killing"] is None


def test_a_house_rule_in_the_template_reaches_the_loaded_power():
    """The whole point: change the .hdt, change what the engine emits."""
    power = KillingAttackRanged()
    assert power.killing is True, "the class's own default"

    power.apply_template(TemplateData(xmlid="RKA", killing=False))

    assert power.killing is False


def test_a_silent_template_leaves_the_class_default_alone():
    power = KillingAttackRanged()

    power.apply_template(TemplateData(xmlid="RKA"))

    assert power.killing is True


@pytest.mark.parametrize("attribute", ["does_body", "does_knockback"])
def test_the_other_combat_facts_travel_the_same_road(attribute):
    """Not just killing -- knockback and BODY are stated by the template too,
    and a campaign that turns one off should not need a code change either."""
    power = KillingAttackRanged()

    power.apply_template(TemplateData(xmlid="RKA", **{attribute: True}))
    assert getattr(power, attribute) is True

    power.apply_template(TemplateData(xmlid="RKA", **{attribute: False}))
    assert getattr(power, attribute) is False
