"""The campaign layer patches TemplateData at the single door.

`TemplateData` is constructed in exactly one file and reached through one
method, so this is the whole interception. Everything downstream --
apply_template, the .hde exporter, kirby-combat's view -- receives a
TemplateData that already carries the campaign's values and needs no knowledge
that campaigns exist.
"""
from __future__ import annotations

import pytest

from kirby_cost.campaign import CampaignRules, use_campaign_rules


def test_without_a_campaign_the_template_is_unchanged(provider):
    assert provider.get_template_data("RKA").killing is True


def test_a_campaign_value_replaces_the_template_value(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with use_campaign_rules(rules):
        assert provider.get_template_data("RKA").killing is False


def test_the_patch_does_not_leak_outside_the_block(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with use_campaign_rules(rules):
        provider.get_template_data("RKA")
    assert provider.get_template_data("RKA").killing is True, \
        "the provider's cached TemplateData was mutated, not copied"


def test_an_untouched_power_is_unaffected(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with use_campaign_rules(rules):
        assert provider.get_template_data("HKA").killing is True


def test_the_patched_template_names_what_the_campaign_forced(provider):
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with use_campaign_rules(rules):
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
    with use_campaign_rules(silent):
        assert provider.get_template_data("RKA").killing is True
        assert provider.get_template_data("RKA").campaign_forced == frozenset()

    says_no = CampaignRules(provider=provider)
    says_no.set("RKA", "killing", False)
    with use_campaign_rules(says_no):
        assert provider.get_template_data("RKA").killing is False


def test_other_fields_survive_the_patch(provider):
    """A patched copy must carry everything the original did -- the .hdt
    experiment showed HD silently zeroing a power when an override replaced
    rather than merged, costing an RKA at 1 instead of 13."""
    before = provider.get_template_data("RKA")
    rules = CampaignRules(provider=provider)
    rules.set("RKA", "killing", False)
    with use_campaign_rules(rules):
        after = provider.get_template_data("RKA")
    assert after.display == before.display
    assert after.base_cost == before.base_cost
    assert after.level_cost == before.level_cost
    assert after.adders == before.adders


def test_a_nested_modifier_definition_is_patched_too(provider):
    """The provider has FOUR doors that hand out TemplateData, not one, and
    `hdc_loader._apply_template_to_modifier` tries `get_nested_modifier`
    FIRST, falling back to `get_template_data` only when it returns None.

    Main6E defines 196 nested modifiers across 59 owner powers -- MULTIFORM
    defines its own COSTSEND -- and all 196 xmlids are also in the flat index,
    so `set()` accepts a rule on them happily. Measured before the fix:
    forcing COSTSEND level_cost=99 gave 99.0 through the flat door and 0.0
    through the nested one, so a GM re-pricing Costs Endurance got it on every
    power EXCEPT the 59 that define it themselves -- accepted, and silently
    dropped."""
    assert provider.get_nested_modifier("MULTIFORM", "COSTSEND") is not None, \
        "Main6E stopped defining MULTIFORM's own COSTSEND; re-measure this"
    rules = CampaignRules(provider=provider)
    rules.set("COSTSEND", "level_cost", 99.0)
    with use_campaign_rules(rules):
        flat = provider.get_template_data("COSTSEND")
        nested = provider.get_nested_modifier("MULTIFORM", "COSTSEND")
        assert flat.level_cost == 99.0
        assert nested.level_cost == 99.0, \
            "the nested door dropped the campaign's rule"
        assert nested.campaign_forced == frozenset({"level_cost"})
    assert provider.get_nested_modifier("MULTIFORM", "COSTSEND").level_cost == 0.0, \
        "the provider's cached nested TemplateData was mutated, not copied"


def test_the_nested_door_keeps_the_owners_own_definition(provider):
    """Patching must not collapse the nested definition into the flat one.
    MULTIFORM's COSTSEND has two options the global one does not; taking the
    global definition for it costs and prints the wrong thing."""
    rules = CampaignRules(provider=provider)
    rules.set("COSTSEND", "level_cost", 99.0)
    with use_campaign_rules(rules):
        nested = provider.get_nested_modifier("MULTIFORM", "COSTSEND")
    assert set(nested.options) == {"ONLYTOCHANGE", "TOSTAYINFORM"}


def test_maneuvers_are_refused_rather_than_accepted_and_dropped(provider):
    """All 53 template maneuvers carry XMLID="MANEUVER" and are keyed by
    DISPLAY, so `hdc_loader` routes them to `get_maneuver` and never calls
    `get_template_data`. "MANEUVER" IS in the flat index (as Basic Strike,
    first wins), so before this change `rules.set("MANEUVER", "killing",
    False)` was accepted and was 100% inert.

    Patching `get_maneuver` by xmlid instead would be worse, not better: one
    MANEUVER rule would rewrite all 53 maneuvers at once. Keying a rule by
    display is a real feature and it is not this one, so the honest answer
    today is to refuse it and say why."""
    rules = CampaignRules(provider=provider)
    with pytest.raises(ValueError) as excinfo:
        rules.set("MANEUVER", "killing", False)
    message = str(excinfo.value)
    assert "MANEUVER" in message
    assert "display" in message.lower()


def test_a_none_value_is_refused(provider):
    """`apply_template` skips a tri-state field whose template value is None
    (`if stated_value is None ... continue`), so a rule that sets None is a
    guaranteed no-op. "Revert to the class default" is not a capability that
    exists, so accepting None would only add another silent-no-op path."""
    rules = CampaignRules(provider=provider)
    with pytest.raises(ValueError) as excinfo:
        rules.set("RKA", "killing", None)
    assert "None" in str(excinfo.value)
