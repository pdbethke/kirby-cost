"""Activation: which purchases count right now, and why."""
from kirby_cost.model.activation import (
    ActivationContext, Contribution, CharacteristicState,
)


def test_an_unconditional_contribution_always_applies():
    c = Contribution(xmlid="DEX", delta=9.0, source_label="Enhanced Reflexes")
    assert c.applies(ActivationContext()) is True
    assert c.applies(ActivationContext(in_hero_id=False)) is True


def test_a_hero_id_contribution_applies_only_in_hero_id():
    c = Contribution(xmlid="DEX", delta=9.0, source_label="Enhanced Reflexes",
                     requires_hero_id=True)
    assert c.applies(ActivationContext(in_hero_id=True)) is True
    assert c.applies(ActivationContext(in_hero_id=False)) is False


def test_the_default_context_is_in_hero_id():
    # A fighting character is overwhelmingly in costume; defaulting the other
    # way would silently weaken every character with conditional purchases.
    assert ActivationContext().in_hero_id is True


def test_state_totals_only_the_active_contributions():
    st = CharacteristicState(
        xmlid="DEX", base=10.0,
        contributions=[
            Contribution("DEX", 9.0, "Enhanced Reflexes", requires_hero_id=True),
            Contribution("DEX", 2.0, "Cybernetic Implant"),
        ],
    )
    assert st.value(ActivationContext(in_hero_id=True)) == 21.0
    assert st.value(ActivationContext(in_hero_id=False)) == 12.0


def test_the_derivation_names_every_active_source():
    st = CharacteristicState(
        xmlid="DEX", base=10.0,
        contributions=[Contribution("DEX", 9.0, "Enhanced Reflexes",
                                    requires_hero_id=True)],
    )
    d = st.derivation(ActivationContext(in_hero_id=True))
    # Pin the whole line, not substrings: "9" alone also matches the rendered
    # total 19, so a flipped sign or a mis-summed delta used to pass here.
    assert d == "DEX 19 = 10 base +9 (Enhanced Reflexes)"


def test_the_derivation_omits_inactive_sources():
    st = CharacteristicState(
        xmlid="DEX", base=10.0,
        contributions=[Contribution("DEX", 9.0, "Enhanced Reflexes",
                                    requires_hero_id=True)],
    )
    assert "Enhanced Reflexes" not in st.derivation(
        ActivationContext(in_hero_id=False))


def test_a_state_with_no_contributions_is_its_base():
    st = CharacteristicState(xmlid="INT", base=23.0, contributions=[])
    assert st.value(ActivationContext()) == 23.0


def test_a_purchase_carrying_the_hero_id_limitation_is_conditional():
    """Ravel's PRE +8 is bought as a power limited to his Hero identity."""
    import json
    from kirby_cost.io.build_json import build_from_json
    from kirby_cost.model.activation import contribution_from_purchase

    hero = build_from_json(json.load(
        open("tests/fixtures/authored/Ravel.json")))
    pre_powers = [p for p in hero.powers
                  if (getattr(p, "xmlid", "") or "").upper() == "PRE"]
    assert pre_powers, "Ravel should buy PRE as a power"

    c = contribution_from_purchase(pre_powers[0])
    assert c is not None
    assert c.xmlid == "PRE"
    assert c.delta == 8.0
    assert c.requires_hero_id is True


def test_a_plain_purchase_is_unconditional():
    import json
    from kirby_cost.io.build_json import build_from_json
    from kirby_cost.model.activation import contribution_from_purchase

    hero = build_from_json(json.load(
        open("tests/fixtures/authored/Ravel.json")))
    section_int = [c for c in hero.characteristics
                   if (getattr(c, "xmlid", "") or "").upper() == "INT"][0]
    c = contribution_from_purchase(section_int)
    assert c is None or c.requires_hero_id is False


def test_a_state_cannot_be_mutated_after_construction():
    """`frozen=True` freezes the attribute; the sequence has to be frozen too."""
    st = CharacteristicState(
        xmlid="DEX", base=10.0,
        contributions=[Contribution("DEX", 9.0, "Enhanced Reflexes")],
    )
    assert isinstance(st.contributions, tuple)
    import pytest
    with pytest.raises(AttributeError):
        st.contributions.append(Contribution("DEX", 100.0, "Cheating"))
    assert st.value(ActivationContext()) == 19.0


# --------------------------------------------------------------------------
# A framework's limitation binds what it holds.
# --------------------------------------------------------------------------

class _FakeMod:
    def __init__(self, xmlid, private=False):
        self.xmlid = xmlid
        self.private = private


class _FakePurchase:
    def __init__(self, xmlid, levels=0, mods=(), parent=None, main_power=None):
        self.xmlid = xmlid
        self.name = ""
        self.levels = levels
        self.assigned_modifiers = list(mods)
        self.parent = parent
        self.main_power = main_power


def test_a_slot_inherits_its_frameworks_hero_id_limitation():
    from kirby_cost.model.activation import contribution_from_purchase

    pool = _FakePurchase("MULTIPOWER", mods=[_FakeMod("OIHID")])
    slot = _FakePurchase("STR", levels=30, parent=pool)
    c = contribution_from_purchase(slot)
    assert c is not None and c.requires_hero_id is True


def test_a_compound_part_inherits_through_two_levels():
    """main_power reaches the compound; the compound's parent is the pool."""
    from kirby_cost.model.activation import contribution_from_purchase

    pool = _FakePurchase("MULTIPOWER", mods=[_FakeMod("OIHID")])
    compound = _FakePurchase("COMPOUNDPOWER", parent=pool)
    part = _FakePurchase("DEX", levels=4, main_power=compound)
    assert contribution_from_purchase(part).requires_hero_id is True


def test_a_pools_private_limitation_does_not_reach_its_slots():
    """A List moves private mods off the shared list; they price the pool."""
    from kirby_cost.model.activation import contribution_from_purchase

    pool = _FakePurchase("VPP", mods=[_FakeMod("OIHID", private=True)])
    slot = _FakePurchase("STR", levels=30, parent=pool)
    assert contribution_from_purchase(slot).requires_hero_id is False


def test_a_slot_of_an_unlimited_framework_is_unconditional():
    from kirby_cost.model.activation import contribution_from_purchase

    pool = _FakePurchase("MULTIPOWER", mods=[_FakeMod("REQUIRESASKILLROLL")])
    slot = _FakePurchase("STR", levels=30, parent=pool)
    assert contribution_from_purchase(slot).requires_hero_id is False


def test_ravels_multipower_slot_inherits_from_the_real_document():
    """Ravel's +30 STR is a slot of a pool bought Only In Alternate Identity.

    The .hdc path is the one that rebuilds framework membership, so this is
    where the inheritance is observable on real data.
    """
    from kirby_cost.io.hdc_loader import HDCLoader
    from kirby_cost.model.activation import contribution_from_purchase

    hero = HDCLoader().load_file("tests/fixtures/authored/Ravel.hdc")
    strs = [p for p in hero.powers
            if (getattr(p, "xmlid", "") or "").upper() == "STR"]
    assert strs, "Ravel should buy STR as a power"
    slot = strs[0]
    assert not [m for m in slot.assigned_modifiers if m.xmlid == "OIHID"], (
        "the slot must NOT carry OIHID itself, or this proves nothing")
    assert slot.parent is not None and slot.parent.xmlid == "MULTIPOWER"
    assert contribution_from_purchase(slot).requires_hero_id is True


# --------------------------------------------------------------------------
# The hero's temporal value.
# --------------------------------------------------------------------------

def test_ravel_is_two_different_characters():
    """The whole point: base is the sheet, temporal is who is fighting."""
    import json
    from kirby_cost.io.build_json import build_from_json
    from kirby_cost.model.activation import ActivationContext

    hero = build_from_json(json.load(
        open("tests/fixtures/authored/Ravel.json")))

    # The base is untouched — this is what costs derive from.
    assert hero.characteristic_value("DEX") == 10.0
    assert hero.characteristic_value("PRE") == 10.0

    civilian = ActivationContext(in_hero_id=False)
    hero_id = ActivationContext(in_hero_id=True)

    assert hero.temporal_characteristic("DEX", civilian) == 10.0
    assert hero.temporal_characteristic("DEX", hero_id) == 19.0
    assert hero.temporal_characteristic("PRE", civilian) == 10.0
    assert hero.temporal_characteristic("PRE", hero_id) == 18.0


def test_an_unconditional_characteristic_is_the_same_either_way():
    """Ravel's INT is bought in the section, so no identity affects it."""
    import json
    from kirby_cost.io.build_json import build_from_json
    from kirby_cost.model.activation import ActivationContext

    hero = build_from_json(json.load(
        open("tests/fixtures/authored/Ravel.json")))
    assert hero.temporal_characteristic("INT",
                                        ActivationContext(in_hero_id=True)) == 23.0
    assert hero.temporal_characteristic("INT",
                                        ActivationContext(in_hero_id=False)) == 23.0


def test_the_state_explains_itself():
    import json
    from kirby_cost.io.build_json import build_from_json
    from kirby_cost.model.activation import ActivationContext

    hero = build_from_json(json.load(
        open("tests/fixtures/authored/Ravel.json")))
    d = hero.characteristic_state("DEX").derivation(ActivationContext())
    assert d == "DEX 19 = 10 base +9 (Enhanced Reflexes)"


def test_the_default_context_is_hero_id():
    import json
    from kirby_cost.io.build_json import build_from_json

    hero = build_from_json(json.load(
        open("tests/fixtures/authored/Ravel.json")))
    assert hero.temporal_characteristic("DEX") == 19.0


def test_the_temporal_value_reads_the_xmlid_case_insensitively():
    import json
    from kirby_cost.io.build_json import build_from_json

    hero = build_from_json(json.load(
        open("tests/fixtures/authored/Ravel.json")))
    assert hero.temporal_characteristic("dex") == 19.0


def test_a_characteristic_nobody_bought_as_a_power_is_just_its_base():
    import json
    from kirby_cost.io.build_json import build_from_json

    hero = build_from_json(json.load(
        open("tests/fixtures/authored/Ravel.json")))
    st = hero.characteristic_state("EGO")
    assert st.contributions == ()
    assert hero.temporal_characteristic("EGO") == hero.characteristic_value("EGO")


def test_the_walk_counts_a_framework_slot_exactly_once():
    """A pool holds its slots in `objects` AND the loader lists them flat."""
    from kirby_cost.io.hdc_loader import HDCLoader

    hero = HDCLoader().load_file("tests/fixtures/authored/Ravel.hdc")
    st = hero.characteristic_state("STR")
    assert len(st.contributions) == 1
    assert st.contributions[0].delta == 30.0
