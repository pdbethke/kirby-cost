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
