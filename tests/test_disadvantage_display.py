"""The four complications HD renders differently, and the name that means two things.

Java gives Enraged, Hunted, Reputation and Susceptibility each their own
150-line ``getColumn2Output``. Diffing them against the generic one shows the
whole difference is four small things, so this port names them as knobs on the
shared renderer rather than copying the method four times — which is what makes
the differences so easy to miss in the Java.

All four had been pass-throughs ending `return super().column2_output`, three
of them with a comment saying "(Simplified - full implementation would match
Java exactly)". Enraged even built its own string first and then discarded it.
"""
from __future__ import annotations

import pytest

from kirby_cost.objects.disads.disadvantage import Disadvantage
from kirby_cost.objects.disads.enraged import Enraged
from kirby_cost.objects.disads.reputation import Reputation
from kirby_cost.objects.disads.susceptibility import Susceptibility
from kirby_cost.objects.perks.reputation import Reputation as ReputationPerk


def test_the_generic_complication_separates_adders_with_a_space_then_commas():
    d = Disadvantage()
    assert d._adder_sep(1, 0) == " "
    assert d._adder_sep(2, 0) == ", "


def test_susceptibility_swaps_them_and_never_counts():
    """Two of HD's changes produce one effect, and either alone would be
    wrong: the separators are swapped AND the counter never advances, so the
    "first adder" branch cannot fire and every adder takes the space. That is
    what puts "per Phase" after the damage with no comma."""
    s = Susceptibility()
    assert s._counts_adders is False
    assert s._adder_sep(0, 0) == " "
    assert s._adder_sep(1, 0) == ", "   # unreachable in practice, pinned anyway


def test_reputation_leads_its_first_required_adder_with_a_comma():
    """"...evil creature, Very Frequently" — the frequency reads as a clause
    about the reputation, not as part of its description."""
    r = Reputation()
    assert r._adder_sep(1, 0, required=True) == ", "
    assert r._adder_sep(1, 0) == " "


def test_reputation_merges_brackets_rather_than_nesting_them():
    r = Reputation()
    assert r._merges_brackets is True


def test_enraged_prints_its_trigger_in_the_head_not_after_the_modifiers():
    e = Enraged()
    assert e._input_after_modifiers is False
    assert e._honours_display_in_string is True


def test_enraged_leads_with_berserk_and_then_suppresses_the_adder():
    """HD prints the BERSERK adder's alias before the trigger text and then
    clears its displayInString flag, so the adder loops do not print it a
    second time. Both halves matter."""
    from kirby_cost.objects.adder import Adder
    e = Enraged()
    e.input = "in combat or when injured"
    berserk = Adder(); berserk.xmlid = "BERSERK"; berserk._alias = "Berserk"
    e._assigned_adders = [berserk]
    assert e._column2_head() == " Berserk in combat or when injured"
    assert berserk.display_in_string is False


def test_an_enraged_with_no_trigger_prints_no_head():
    assert Enraged()._column2_head() == ""


# ── the collision ──────────────────────────────────────────────────────

def test_reputation_is_two_different_objects():
    """A Perk and a Disadvantage share the xmlid REPUTATION and have
    completely different adders — RECOGNIZED/EXTREME against HOWWIDE/HOWWELL.
    The template index is first-wins, so without a section the perk owned the
    name and a Negative Reputation was rendered against the wrong template."""
    assert ReputationPerk is not Reputation
    from kirby_cost.io.hdc_loader import _template_section
    assert _template_section(Reputation()) == "disadvantages"
    assert _template_section(ReputationPerk()) == "perks"
    assert _template_section(None) is None
    assert _template_section(Disadvantage()) == "disadvantages"


def test_the_provider_serves_each_section_its_own_definition(provider):
    disad = provider.get_template_data("REPUTATION", "disadvantages")
    perk = provider.get_template_data("REPUTATION", "perks")
    assert set(disad.adders) == {"RECOGNIZED", "EXTREME", "NOTALL"}
    assert set(perk.adders) == {"HOWWIDE", "HOWWELL"}


@pytest.fixture
def provider():
    from kirby_cost.template.hdt_provider import HDTTemplateProvider
    try:
        return HDTTemplateProvider()
    except FileNotFoundError:
        pytest.skip("no .hdt configured")
