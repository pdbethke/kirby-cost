"""A campaign's power level, as an object the engine can hold a build to.

Character-workshop spec §5.2: "is this inside the power level" is a rule, so
it lives in the engine and not in a critic's prompt. These tests pin the
objects alone; `test_builder_limits_judged.py` pins what `judge` makes of
them.
"""
from __future__ import annotations

import pytest

from kirby_cost.builder import Limit, LimitError, PowerLevel, Template


def test_a_power_level_states_every_field():
    pl = PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                    (Limit(Limit.Kind.ACTIVE_POINTS, 60, None),))
    assert pl.template is Template.SUPERHEROIC
    assert (pl.base_points, pl.disad_points, pl.experience) == (400, 0, 0)
    assert pl.limits[0].maximum == 60


def test_a_characteristic_limit_names_its_characteristic():
    with pytest.raises(LimitError, match="CHARACTERISTIC_MAX needs a characteristic"):
        Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, None)
    assert Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "spd").characteristic == "SPD"


def test_only_a_characteristic_limit_names_a_characteristic():
    with pytest.raises(LimitError, match="ACTIVE_POINTS takes no characteristic"):
        Limit(Limit.Kind.ACTIVE_POINTS, 60, "STR")


def test_a_limit_is_not_negative():
    with pytest.raises(LimitError, match="maximum"):
        Limit(Limit.Kind.DAMAGE_CLASSES, -1, None)


def test_a_limits_kind_is_a_kind():
    with pytest.raises(LimitError, match="Limit.Kind"):
        Limit("ACTIVE_POINTS", 60, None)


def test_two_limits_of_one_kind_are_refused():
    """Review Focus 4: never resolved by taking the first."""
    with pytest.raises(LimitError, match="ACTIVE_POINTS.*twice"):
        PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                   (Limit(Limit.Kind.ACTIVE_POINTS, 60, None),
                    Limit(Limit.Kind.ACTIVE_POINTS, 75, None)))
    with pytest.raises(LimitError, match="SPD.*twice"):
        PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                   (Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "SPD"),
                    Limit(Limit.Kind.CHARACTERISTIC_MAX, 5, "spd")))


def test_caps_on_two_characteristics_are_two_limits():
    pl = PowerLevel(Template.SUPERHEROIC, 400, 0, 0,
                    (Limit(Limit.Kind.CHARACTERISTIC_MAX, 6, "SPD"),
                     Limit(Limit.Kind.CHARACTERISTIC_MAX, 8, "OCV")))
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
