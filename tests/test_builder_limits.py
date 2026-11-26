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
                    (Limit(Limit.Kind.ACTIVE_POINTS, 60, None, None),))
    assert pl.template is Template.SUPERHEROIC
    assert (pl.base_points, pl.disad_points, pl.experience) == (400, 0, 0)
    assert pl.limits[0].maximum == 60


def test_a_characteristic_limit_names_its_characteristic():
    with pytest.raises(LimitError, match="CHARACTERISTIC_MAX needs a characteristic"):
        Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, None, None)
    assert Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "spd", None).characteristic == "SPD"


def test_only_a_characteristic_limit_names_a_characteristic():
    with pytest.raises(LimitError, match="ACTIVE_POINTS takes no characteristic"):
        Limit(Limit.Kind.ACTIVE_POINTS, 60, "STR", None)


def test_a_limit_is_not_negative():
    with pytest.raises(LimitError, match="maximum"):
        Limit(Limit.Kind.DAMAGE_CLASSES, -1, None, None)


def test_a_limits_kind_is_a_kind():
    with pytest.raises(LimitError, match="Limit.Kind"):
        Limit("ACTIVE_POINTS", 60, None, None)


def test_two_limits_of_one_kind_are_refused():
    """Review Focus 4: never resolved by taking the first."""
    with pytest.raises(LimitError, match="ACTIVE_POINTS.*twice"):
        PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                   (Limit(Limit.Kind.ACTIVE_POINTS, 60, None, None),
                    Limit(Limit.Kind.ACTIVE_POINTS, 75, None, None)))
    with pytest.raises(LimitError, match="SPD.*twice"):
        PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                   (Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "SPD", None),
                    Limit(Limit.Kind.CHARACTERISTIC_MAX, 5, "spd", None)))


def test_caps_on_two_characteristics_are_two_limits():
    pl = PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                    (Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "SPD", None),
                     Limit(Limit.Kind.CHARACTERISTIC_MAX, 8, "OCV", None)))
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
        Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, None)
    dc = Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, BOOK_DAMAGE_ADVANTAGES)
    assert dc.counts == BOOK_DAMAGE_ADVANTAGES
    assert Limit(Limit.Kind.DAMAGE_CLASSES, 12, None, ()).counts == ()


def test_only_a_damage_class_limit_states_advantages():
    with pytest.raises(LimitError, match="ACTIVE_POINTS takes no Advantages"):
        Limit(Limit.Kind.ACTIVE_POINTS, 60, None, ())


def test_the_books_list_names_options_and_adders_where_the_book_does():
    """'Usable As Attack' is Usable On Others' UAA option; 'Boostable
    Charges' is Charges with the Boostable adder (6E2 100)."""
    assert DamageAdvantage("UOO", "UAA", None) in BOOK_DAMAGE_ADVANTAGES
    assert DamageAdvantage("CHARGES", None, "BOOSTABLE") in BOOK_DAMAGE_ADVANTAGES
    assert DamageAdvantage("ARMORPIERCING", None, None) in BOOK_DAMAGE_ADVANTAGES
    assert not [a for a in BOOK_DAMAGE_ADVANTAGES if a.xmlid == "REDUCEDEND"]
