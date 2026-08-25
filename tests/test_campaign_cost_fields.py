"""Which campaign-rule fields actually reprice a loaded object, and which don't.

Task 4 made every non-bookkeeping `TemplateData` field "overridable" in the
sense that `CampaignRules.set()` accepted it. Measured against a real
character load (see the task-5 brief), that was optimistic: `apply_template`
only WIRES a handful of those fields into the loaded object. Accepting a field
it never reads means a GM writes a rule, `set()` says nothing is wrong, and the
rule silently does nothing forever -- the exact defect this whole feature
exists to remove.

This module locks in the one field-level correction Task 5 makes:
`OVERRIDABLE_FIELDS` still derives from `TemplateData`, but a documented
`_UNSUPPORTED_FIELDS` subset is refused at `set()` time, with its own message
naming why (and, where there is one, the field to use instead).
"""
from __future__ import annotations

import dataclasses

import pytest

from kirby_cost.campaign import CampaignRules, use_campaign_rules
from kirby_cost.campaign.rules import (
    OVERRIDABLE_FIELDS,
    _NOT_OVERRIDABLE,
    _UNSUPPORTED_FIELDS,
)
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.template.dataclasses import TemplateData
from tests.corpus import authored_hdc


def _find(hero, xmlid: str):
    """The first loaded object with this xmlid, walking sub_powers/powers."""
    def walk(objects):
        for obj in objects or ():
            if getattr(obj, "xmlid", None) == xmlid:
                return obj
            found = walk(getattr(obj, "powers", None))
            if found is not None:
                return found
        return None

    for section in ("powers", "skills", "talents", "perks", "complications",
                    "martial_arts"):
        found = walk(getattr(hero, section, None))
        if found is not None:
            return found
    return None


@pytest.mark.skipif(
    authored_hdc("Ravel") is None,
    reason="KIRBY_COST_AUTHORED unset, or Ravel is not in it",
)
def test_forcing_level_cost_reprices_the_power(provider):
    """The capability that actually works, locked in end to end.

    Measured (task-5 brief) on Ravel's RKA loaded through HDCLoader:
    level_cost=15.0, levels=2, active_cost=45; forcing level_cost=10.0 moves
    active_cost to 30. That 45->30 is what this test locks in.

    The expected number is a MEASUREMENT, not a re-derived formula. The
    obvious guess -- active_cost = levels * level_cost -- is wrong here: this
    RKA carries a PENETRATING advantage (+1/2), so the engine's real chain is
    active_cost = (levels * level_cost) * (1 + 0.5) = 30 * 1.5 = 45, and a
    formula in the test would have to reproduce that multiplier to be
    trustworthy. Encoding the concrete numbers instead -- and asserting they
    still hold as a *relationship* (45 at the template's level_cost, 30 at the
    forced one) -- is honest about being a snapshot of one build, which is
    what a regression test on a fixed, non-redistributed character actually
    is. If Ravel's RKA build ever changes, this test is meant to fail and be
    re-measured, not silently keep passing against a formula that happens to
    fit.
    """
    hdc = authored_hdc("Ravel")

    # Establish the untouched shape first, so both assertions below are
    # provably about the SAME power, not two different objects that merely
    # share an xmlid.
    baseline = HDCLoader().load_file(str(hdc))
    rka = _find(baseline, "RKA")
    assert rka is not None, "Ravel's RKA moved or was renamed"
    assert rka.levels == 2, "the measurement below assumes this exact build"
    assert rka.active_cost == 45, "the measurement below assumes this exact build"

    forced_level_cost = 10.0
    template_level_cost = provider.get_template_data("RKA").level_cost
    assert forced_level_cost != template_level_cost, \
        "the forced value must differ from the template's to prove anything"

    rules = CampaignRules(provider=provider)
    rules.set("RKA", "level_cost", forced_level_cost)
    with use_campaign_rules(rules):
        hero = HDCLoader().load_file(str(hdc))
        forced = _find(hero, "RKA")

    # Measured directly (see the docstring): forcing level_cost to 10.0 moves
    # this power's active_cost from 45 to 30, not to the 20 that
    # `levels * level_cost` alone would predict.
    assert forced.active_cost == 30
    assert forced.active_cost != rka.active_cost


def test_an_unsupported_field_is_refused_with_its_reason(provider):
    rules = CampaignRules(provider=provider)
    with pytest.raises(ValueError, match="level_cost"):
        rules.set("RKA", "base_cost", 25.0)


def test_an_unsupported_field_is_not_reported_as_a_typo(provider):
    """A field that is refused because it is INERT is a different failure
    from a field that is refused because it does not exist -- a GM must be
    able to tell "this cannot possibly work" apart from "you misspelled it"."""
    rules = CampaignRules(provider=provider)
    with pytest.raises(ValueError) as excinfo:
        rules.set("RKA", "base_cost", 25.0)
    message = str(excinfo.value)
    assert "not a template field" not in message
    assert "Did you mean" not in message


@pytest.mark.parametrize("field", sorted(_UNSUPPORTED_FIELDS))
def test_every_unsupported_field_is_actually_rejected(provider, field):
    """Parametrised over `_UNSUPPORTED_FIELDS` itself, so adding a name to
    that dict without wiring the rejection into `set()` is impossible."""
    rules = CampaignRules(provider=provider)
    with pytest.raises(ValueError):
        rules.set("RKA", field, "anything")


#: field -> a plausible value of the right type, for the "still accepted"
#: check below. The value itself doesn't matter -- only that `set()` does not
#: raise. Must cover EVERY name in `OVERRIDABLE_FIELDS`; the test below
#: parametrises over that set rather than over this dict, so a new
#: `TemplateData` field shows up as a failure here instead of quietly going
#: unchecked. That was the defect in the hand-written version: it listed six
#: of the fifteen fields then wired, and nothing noticed the other nine.
_EFFECTIVE_FIELD_VALUES = {
    "killing": True,
    "does_body": True,
    "does_damage": True,
    "does_knockback": False,
    "defense": "NORMAL",
    "display": "House Blast",
    "level_cost": 10.0,
    "level_value": 1.0,
    "level_power": 1,
    "level_multiplier": 1,
    "min_set": True,
    "max_set": True,
    "range": "LOS",
    "target": "DCV",
    "uses_end": True,
    "base_value": 12.0,
    "all_cost": 5.0,
    "group_cost": 5.0,
    "sense_cost": 5.0,
    "adders": {},
    "options": {},
    "option_aliases": {},
    "types": ("SPECIAL",),
    "attributes": {"DEFENSE": "NORMAL"},
}


@pytest.mark.parametrize("field", sorted(OVERRIDABLE_FIELDS))
def test_the_effective_fields_are_still_accepted(provider, field):
    """Guards against over-broad subtraction: every field NOT in
    `_UNSUPPORTED_FIELDS` was measured to reach a loaded object (see the
    field-by-field record in kirby_cost/campaign/rules.py), so every one of
    them must stay settable.

    Parametrised over `OVERRIDABLE_FIELDS` itself, matching its sibling
    `test_every_unsupported_field_is_actually_rejected`: the set maintains
    the test rather than the other way round."""
    assert field in _EFFECTIVE_FIELD_VALUES, (
        f"{field!r} became overridable and nobody checked it is accepted. "
        f"Give it a plausible value above -- or, if forcing it turns out to "
        f"change nothing, add it to _UNSUPPORTED_FIELDS with the measurement."
    )
    rules = CampaignRules(provider=provider)
    rules.set("RKA", field, _EFFECTIVE_FIELD_VALUES[field])


def test_overridable_fields_is_still_derived():
    """The derivation, not a hand list -- so a new `TemplateData` fact becomes
    overridable automatically, and only the documented exceptions are cut.

    This test OWNS the exact-exclusions contract: it pins the full expression,
    `_UNSUPPORTED_FIELDS` included. `tests/test_campaign_rules.py`'s
    `test_the_overridable_fields_come_from_templatedata_not_a_hand_list` keeps
    its original, looser job -- proving the set is derived at all -- so the
    two tests do not duplicate each other.
    """
    all_fields = frozenset(f.name for f in dataclasses.fields(TemplateData))
    assert OVERRIDABLE_FIELDS == (
        all_fields - _NOT_OVERRIDABLE - frozenset(_UNSUPPORTED_FIELDS)
    )
