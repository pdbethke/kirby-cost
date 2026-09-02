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

    RE-DERIVED: this slot is also ``AFFECTS_TOTAL="No"``, so it now yields no
    contribution at all and the old assertion (``.requires_hero_id is True``)
    can no longer be written — it would raise on None. The inheritance itself
    is unchanged and still worth proving on the real document, so the test
    asserts the predicate directly, then pins the interaction: HD's exclusion
    wins over an inherited condition, because a purchase HD keeps out of the
    total contributes nothing to condition.
    """
    from kirby_cost.io.hdc_loader import HDCLoader
    from kirby_cost.model.activation import (
        _has_hero_id_limitation, contribution_from_purchase,
    )

    hero = HDCLoader().load_file("tests/fixtures/authored/Ravel.hdc")
    strs = [p for p in hero.powers
            if (getattr(p, "xmlid", "") or "").upper() == "STR"]
    assert strs, "Ravel should buy STR as a power"
    slot = strs[0]
    assert not [m for m in slot.assigned_modifiers if m.xmlid == "OIHID"], (
        "the slot must NOT carry OIHID itself, or this proves nothing")
    assert slot.parent is not None and slot.parent.xmlid == "MULTIPOWER"
    assert _has_hero_id_limitation(slot) is True
    assert slot.affect_total is False
    assert contribution_from_purchase(slot) is None


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


def test_the_walk_counts_a_framework_slot_exactly_once(monkeypatch):
    """A pool holds its slots in `objects` AND the loader lists them flat.

    RE-DERIVED: this used to count the contributions the slot produced, which
    stopped working when HD's own AFFECTS_TOTAL="No" removed the slot from the
    total — a walk that visited it twice would now read zero either way, so
    the old assertion could no longer fail. Counting VISITS instead keeps the
    double-counting guard on the real document and makes it independent of
    whether the slot contributes.
    """
    from kirby_cost.io import hdc_loader as loader_mod
    from kirby_cost.io.hdc_loader import HDCLoader
    from kirby_cost.model import activation

    hero = HDCLoader().load_file("tests/fixtures/authored/Ravel.hdc")
    slot = next(p for p in hero.powers
                if (p.name or "").strip() == "Reinforced String")
    assert slot.parent is not None and slot.parent.xmlid == "MULTIPOWER", (
        "the fixture must still hold this STR as a POOLED slot")

    visits = []
    real = activation.contribution_from_purchase

    def counting(obj):
        visits.append(id(obj))
        return real(obj)

    monkeypatch.setattr(activation, "contribution_from_purchase", counting)
    monkeypatch.setattr(loader_mod, "contribution_from_purchase", counting,
                        raising=False)
    hero.characteristic_state("STR")

    assert visits, "the walk visited nothing — the spy is not wired in"
    assert visits.count(id(slot)) == 1


# ── HD's own totals flags ───────────────────────────────────────────────────
# AFFECTS_PRIMARY / AFFECTS_TOTAL are how HD records whether a purchase
# raises the character's characteristic or merely sits on the sheet as a
# situational ability. A purchase HD excludes from the total is situational
# by construction, and the situation is what v1 does not model — so counting
# it would give the character a permanent bonus their sheet does not.


class _Purchase:
    """The smallest thing contribution_from_purchase reads."""

    def __init__(self, xmlid, levels, name="", affect_total=True):
        self.xmlid = xmlid
        self.levels = levels
        self.name = name
        self.affect_total = affect_total
        self.assigned_modifiers = []


def test_a_purchase_hd_excludes_from_the_total_contributes_nothing():
    from kirby_cost.model.activation import contribution_from_purchase

    tail = _Purchase("STR", 20, name="Tail", affect_total=False)
    assert contribution_from_purchase(tail) is None


def test_a_purchase_hd_counts_toward_the_total_still_contributes():
    from kirby_cost.model.activation import contribution_from_purchase

    c = contribution_from_purchase(_Purchase("STR", 30, name="Wolf Strength"))
    assert c is not None
    assert c.delta == 30.0 and c.source_label == "Wolf Strength"


def test_an_object_with_no_totals_flags_still_contributes():
    """Only a CharAffectingObject carries the flags; everything else keeps
    the class default of True rather than silently dropping out."""
    from kirby_cost.model.activation import contribution_from_purchase

    class _Flagless:
        xmlid, levels, name = "DEX", 5, "Nimble"
        assigned_modifiers = ()

    assert contribution_from_purchase(_Flagless()) is not None


def test_ravels_pooled_str_slot_is_excluded_by_hds_own_flag():
    """"Reinforced String" is AFFECTS_PRIMARY="No" AFFECTS_TOTAL="No".

    It is a Multipower slot: one allocation of nineteen, and HD does not add
    it to Ravel's STR. The docstring on ``characteristic_state`` used to warn
    that a pooled slot OVERSTATES the character — for this slot the warning is
    now unnecessary, because HD already said it does not count.
    """
    from kirby_cost.io.hdc_loader import HDCLoader

    hero = HDCLoader().load_file("tests/fixtures/authored/Ravel.hdc")
    slot = next(p for p in hero.powers
                if (p.name or "").strip() == "Reinforced String")
    assert slot.affect_total is False, "fixture no longer has the flag"

    st = hero.characteristic_state("STR")
    assert [c.source_label for c in st.contributions] == []
    assert st.value(ActivationContext(in_hero_id=True)) == st.base


def test_the_build_doc_carries_hds_totals_flags():
    """A rebuild that drops AFFECTS_PRIMARY/AFFECTS_TOTAL is a different character.

    kirby-api stores the build doc relationally and rebuilds from it. The flags
    were not in the doc, so a rebuilt object took the class default (True) and
    counted a purchase HD keeps out of the totals: `Cobra.hdc` has a +2 DCV
    power marked AFFECTS_TOTAL="No", and the database came back DCV 12 where
    the canonical load says 10.

    Emitted only when False, since True is the default on both — a character
    with nothing situational produces the same doc as before.
    """
    from kirby_cost.io.build_json import build_from_json, to_build_json
    from kirby_cost.io.formats import load_build

    hero = load_build("tests/fixtures/authored/Ravel.hdc", format="hdc")
    doc = to_build_json(hero)

    slot = next(o for o in doc["powers"]
                if (o.get("name") or "").strip() == "Reinforced String")
    assert slot["affects_primary"] is False
    assert slot["affects_total"] is False
    # Unremarkable purchases stay quiet.
    plain = next(o for o in doc["powers"]
                 if (o.get("name") or "").strip() == "Enhanced Reflexes")
    assert "affects_total" not in plain and "affects_primary" not in plain

    # And the rebuild agrees with the original about what counts.
    again = build_from_json(doc)
    for xmlid in ("STR", "DEX", "SPD", "DCV"):
        assert (again.temporal_characteristic(xmlid)
                == hero.temporal_characteristic(xmlid)), xmlid
