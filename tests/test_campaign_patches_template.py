"""The campaign layer patches TemplateData at the single door.

`TemplateData` is constructed in exactly one file and reached through one
method, so this is the whole interception. Everything downstream --
apply_template, the .hde exporter, kirby-combat's view -- receives a
TemplateData that already carries the campaign's values and needs no knowledge
that campaigns exist.
"""
from __future__ import annotations

from kirby_cost.campaign import CampaignRules, campaign_rules


def test_without_a_campaign_the_template_is_unchanged(provider):
    assert provider.get_template_data("RKA").killing is True


def test_a_campaign_value_replaces_the_template_value(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with campaign_rules(rules):
        assert provider.get_template_data("RKA").killing is False


def test_the_patch_does_not_leak_outside_the_block(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with campaign_rules(rules):
        provider.get_template_data("RKA")
    assert provider.get_template_data("RKA").killing is True, \
        "the provider's cached TemplateData was mutated, not copied"


def test_an_untouched_power_is_unaffected(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with campaign_rules(rules):
        assert provider.get_template_data("HKA").killing is True


def test_the_patched_template_names_what_the_campaign_forced(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with campaign_rules(rules):
        assert provider.get_template_data("RKA").campaign_forced == frozenset({"killing"})
    assert provider.get_template_data("RKA").campaign_forced == frozenset()


def test_a_campaign_that_says_false_differs_from_one_that_is_silent(provider):
    """The tri-state, at the campaign layer. `killing=False` is an ANSWER;
    not mentioning killing is an ABSENCE, and they must not collapse. The
    template flags already work this way (TemplateData.killing is
    Optional[bool]) and combat's xmlid fallback depends on the distinction --
    if a silent campaign patched killing to a default, every killing attack
    in every campaign would quietly disarm."""
    silent = CampaignRules(provider=provider)
    with campaign_rules(silent):
        assert provider.get_template_data("RKA").killing is True
        assert provider.get_template_data("RKA").campaign_forced == frozenset()

    says_no = CampaignRules(provider=provider)
    says_no.set("RKA", "killing", False)
    with campaign_rules(says_no):
        assert provider.get_template_data("RKA").killing is False


def test_other_fields_survive_the_patch(provider):
    """A patched copy must carry everything the original did -- the .hdt
    experiment showed HD silently zeroing a power when an override replaced
    rather than merged, costing an RKA at 1 instead of 13."""
    before = provider.get_template_data("RKA")
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with campaign_rules(rules):
        after = provider.get_template_data("RKA")
    assert after.display == before.display
    assert after.base_cost == before.base_cost
    assert after.level_cost == before.level_cost
    assert after.adders == before.adders
