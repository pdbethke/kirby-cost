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
    assert "10" in d and "9" in d and "Enhanced Reflexes" in d


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
