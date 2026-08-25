"""A campaign's rules are a DIFF, and a bad one is refused at the line that wrote it."""
from __future__ import annotations

import pytest

from kirby_cost.campaign.rules import CampaignRules, OVERRIDABLE_FIELDS


def test_a_rule_is_stored_and_read_back(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    assert rules.get("RKA", "killing") is False


def test_the_overridable_fields_come_from_templatedata_not_a_hand_list():
    """A second list would drift. Adding a template fact must make it
    overridable automatically -- that is the defect this whole line of work
    came from: a fact parsed into one structure and dropped because another
    had no field for it. `campaign_forced` is excluded because the provider
    writes it, rather than a GM."""
    import dataclasses
    from kirby_cost.template.dataclasses import TemplateData
    expected = frozenset(f.name for f in dataclasses.fields(TemplateData)) - {"campaign_forced"}
    assert OVERRIDABLE_FIELDS == expected


def test_an_unknown_field_is_refused_at_set_time(provider):
    rules = CampaignRules(provider=provider)
    with pytest.raises(ValueError) as excinfo:
        rules.set("RKA", "kiling", False)
    assert "kiling" in str(excinfo.value)
    assert "killing" in str(excinfo.value), "the message should name the near miss"


def test_an_unknown_xmlid_is_refused_at_set_time(provider):
    rules = CampaignRules(provider=provider)
    with pytest.raises(ValueError) as excinfo:
        rules.set("NOTAPOWER", "killing", False)
    assert "NOTAPOWER" in str(excinfo.value)


def test_a_legal_but_unused_xmlid_is_accepted(provider):
    """A campaign may state a rule for a power no character happens to own."""
    rules = CampaignRules(provider=provider)
    rules.set("MULTIFORM", "killing", False)
    assert rules.get("MULTIFORM", "killing") is False


def test_items_enumerates_the_whole_diff(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    rules.set("HKA", "killing", False)
    assert sorted(rules.items()) == [("HKA", "killing", False), ("RKA", "killing", False)]


def test_an_empty_rule_set_is_falsey(provider):
    assert not CampaignRules(provider=provider)
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    assert rules
