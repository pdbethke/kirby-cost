"""A campaign's power level, as an object the engine can hold a build to.

Character-workshop spec §5.2: "is this inside the power level" is a rule, so
it lives in the engine, not with whoever reviews a build. These tests pin the
objects alone; `test_builder_limits_judged.py` pins what `judge` makes of
them.
"""
from __future__ import annotations

import pytest

from kirby_cost.builder import (
    BOOK_DAMAGE_ADVANTAGES, DamageAdvantage, Limit, LimitError, PowerLevel,
    Template,
)


def test_a_power_level_states_every_field():
    pl = PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                    (Limit(Limit.Kind.ACTIVE_POINTS, 60, None, None, None, None),))
    assert pl.template is Template.SUPERHEROIC
    assert (pl.base_points, pl.disad_points, pl.experience) == (400, 0, 0)
    assert pl.limits[0].maximum == 60


def test_a_characteristic_limit_names_its_characteristic():
    with pytest.raises(LimitError, match="CHARACTERISTIC_MAX needs a characteristic"):
        Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, None, None, None, None)
    assert Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "spd", None, None, None).characteristic == "SPD"


def test_only_a_characteristic_limit_names_a_characteristic():
    with pytest.raises(LimitError, match="ACTIVE_POINTS takes no characteristic"):
        Limit(Limit.Kind.ACTIVE_POINTS, 60, "STR", None, None, None)


def test_a_limit_is_not_negative():
    with pytest.raises(LimitError, match="maximum"):
        Limit(Limit.Kind.DAMAGE_CLASSES, -1, None, None, False, ())


def test_a_limits_kind_is_a_kind():
    with pytest.raises(LimitError, match="Limit.Kind"):
        Limit("ACTIVE_POINTS", 60, None, None, None, None)


def test_two_limits_of_one_kind_are_refused():
    """Review Focus 4: never resolved by taking the first."""
    with pytest.raises(LimitError, match="ACTIVE_POINTS.*twice"):
        PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                   (Limit(Limit.Kind.ACTIVE_POINTS, 60, None, None, None, None),
                    Limit(Limit.Kind.ACTIVE_POINTS, 75, None, None, None, None)))
    with pytest.raises(LimitError, match="SPD.*twice"):
        PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                   (Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "SPD", None, None, None),
                    Limit(Limit.Kind.CHARACTERISTIC_MAX, 5, "spd", None, None, None)))


def test_caps_on_two_characteristics_are_two_limits():
    pl = PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                    (Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "SPD", None, None, None),
                     Limit(Limit.Kind.CHARACTERISTIC_MAX, 8, "OCV", None, None, None)))
    assert len(pl.limits) == 2


def test_points_are_not_negative():
    with pytest.raises(LimitError, match="base_points"):
        PowerLevel(Template.SUPERHEROIC, -1, 0, 0, ())


def test_the_template_is_a_template():
    with pytest.raises(LimitError, match="Template"):
        PowerLevel("builtIn.Superheroic6E.hdt", 400, 0, 0, ())


def test_limits_are_a_tuple():
    with pytest.raises(LimitError, match="tuple"):
        PowerLevel(Template.SUPERHEROIC, 400, 0, 0, [])


def test_a_damage_class_limit_states_which_advantages_count():
    """6E2 100: which Advantages count toward DCs is the GM's decision."""
    with pytest.raises(LimitError, match="DAMAGE_CLASSES needs the Advantages"):
        Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, None, False, ())
    dc = Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, BOOK_DAMAGE_ADVANTAGES, False, ())
    assert dc.counts == BOOK_DAMAGE_ADVANTAGES
    assert Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, (), False, ()).counts == ()


def test_only_a_damage_class_limit_states_advantages():
    with pytest.raises(LimitError, match="ACTIVE_POINTS takes no counts"):
        Limit(Limit.Kind.ACTIVE_POINTS, 60, None, (), None, None)


def test_the_books_list_names_options_and_adders_where_the_book_does():
    """'Usable As Attack' is Usable On Others' UAA option; 'Boostable
    Charges' is Charges with the Boostable adder (6E2 100)."""
    assert DamageAdvantage("UOO", "UAA", None) in BOOK_DAMAGE_ADVANTAGES
    assert DamageAdvantage("CHARGES", None, "BOOSTABLE") in BOOK_DAMAGE_ADVANTAGES
    assert DamageAdvantage("ARMORPIERCING", None, None) in BOOK_DAMAGE_ADVANTAGES
    assert not [a for a in BOOK_DAMAGE_ADVANTAGES if a.xmlid == "REDUCEDEND"]


def test_megascale_counts():
    """6E2 100 counts MegaScale only 'in some instances'; Peter, 2026-11-26:
    'megascale is often used', so the list counts it and a GM who rules it
    out for an attack trims it."""
    assert DamageAdvantage("MEGASCALE", None, None) in BOOK_DAMAGE_ADVANTAGES


def test_a_damage_class_limit_states_doubling_and_its_adders():
    """6E2 101: doubling is a guideline the GM may overrule; 6E2 285 does
    not say which Adding Damage methods a ceiling counts. Both are stated."""
    from kirby_cost.builder import AddedDamage
    with pytest.raises(LimitError, match="doubling stated"):
        Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, (), None, ())
    with pytest.raises(LimitError, match="Adding Damage methods it counts"):
        Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, (), True, None)
    with pytest.raises(LimitError, match="named twice"):
        Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, (), True,
              (AddedDamage.STR, AddedDamage.STR))
    with pytest.raises(LimitError, match="takes no doubling"):
        Limit(Limit.Kind.ACTIVE_POINTS, 60, None, None, True, None)
