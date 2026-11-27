"""Velocity a Move Through can bring (6E2 72, 27; 6E1 157, 245) and weapons
for Weapon Elements (6E2 94, 102; 6E1 378-379). Workshop plan 1b tasks 2-3."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from kirby_cost.engine.csl import Reach
from kirby_cost.engine.movement import (
    best_move_through_velocity, move_through_velocities, noncombat_multiplier,
    phase_velocity,
)
from kirby_cost.engine.weapons import element_reach, is_weapon
from kirby_cost.io.formats import load_build
from tests.corpus import require_authored_hdc


def _load(name):
    return load_build(str(require_authored_hdc(name)), format="hdc")


def _obj(xmlid, levels=0, adders=(), mods=(), parent=None, name=""):
    return SimpleNamespace(
        xmlid=xmlid, levels=levels, name=name, parent=parent, id=f"id-{xmlid}",
        assigned_adders=[SimpleNamespace(xmlid=a, levels=n) for a, n in adders],
        assigned_modifiers=[SimpleNamespace(xmlid=m) for m in mods])


# -- Noncombat multiple (6E1 157) -------------------------------------------

def test_noncombat_is_double_for_free():
    assert noncombat_multiplier(_obj("FLIGHT", 20)) == 2


def test_each_improved_noncombat_level_doubles_again():
    """HD's 'x4 Noncombat' is LEVELS 1."""
    assert noncombat_multiplier(_obj("FLIGHT", 20, adders=[("IMPROVEDNONCOMBAT", 1)])) == 4
    assert noncombat_multiplier(_obj("FLIGHT", 20, adders=[("IMPROVEDNONCOMBAT", 3)])) == 16


def test_no_noncombat_movement_is_one():
    assert noncombat_multiplier(_obj("FLIGHT", 20, mods=["NONONCOMBAT"])) == 1


def test_a_noncombat_leap_spreads_its_distance_over_its_phases():
    """6E1 245: El Salto's Leaping 50m at x32 covers 1,600m over five
    Phases (five doublings): 320m a Phase."""
    assert phase_velocity("LEAPING", 50, 32) == 320
    assert phase_velocity("FLIGHT", 50, 32) == 1600


# -- The best velocity on a build -------------------------------------------

def test_ravels_fastest_is_his_noncombat_flight():
    """Floating String Form (12m) has no Noncombat movement; String Slide
    (13m) doubles to 26m."""
    v = best_move_through_velocity(_load("Ravel"), in_hero_id=True)
    assert (v.xmlid, v.meters) == ("FLIGHT", 26)


def test_powerlads_leap_is_read_off_his_leaping_total():
    """Leaping 70m (his slot rides on the characteristic), x4 Noncombat:
    280m over two Phases."""
    v = best_move_through_velocity(_load("PowerLad"), in_hero_id=True)
    assert (v.xmlid, v.meters, v.hd_id) == ("LEAPING", 140, None)


def test_a_velocity_names_the_multipower_slot_it_needs():
    """6E1 404-405: a slot's movement is there only while its share of the
    reserve is. Ravel's String Slide is a Fixed slot; Floating String Form
    is in no framework."""
    by_name = {}
    for v in move_through_velocities(_load("Ravel"), in_hero_id=True):
        by_name[v.hd_id] = v
    slide, floating = by_name["1669689380740"], by_name["1648500148181"]
    assert slide.meters == 26 and [s.points for s in slide.shares] == [45]
    assert floating.meters == 12 and floating.shares == ()


def test_powerlads_leap_with_and_without_his_multipower_slot():
    """His Leaping 70m carries Iron Grasshopper (+69m, x4 Noncombat), a
    Brick Tricks slot of 44.5 Active Points, a 44-point share (.5 rounds in
    his favour, 6E1 14). On: 280m over two Phases. Off: his own 1m at the
    free x2."""
    leaps = [v for v in move_through_velocities(_load("PowerLad"), in_hero_id=True)
             if v.xmlid == "LEAPING"]
    assert sorted((v.meters, tuple(s.points for s in v.shares)) for v in leaps) == [
        (2.0, ()), (140.0, (44,))]


@pytest.mark.parametrize("xmlid", ["TELEPORTATION", "EXTRADIMENSIONALMOVEMENT", "FTL"])
def test_movement_a_move_through_may_not_use_brings_nothing(xmlid):
    hero = SimpleNamespace(powers=[_obj(xmlid, 100)], equipment=[], characteristics=[])
    assert best_move_through_velocity(hero, in_hero_id=True) is None


def test_megascaled_movement_brings_nothing():
    hero = SimpleNamespace(powers=[_obj("FLIGHT", 40, mods=["MEGASCALE"])],
                           equipment=[], characteristics=[])
    assert best_move_through_velocity(hero, in_hero_id=True) is None


# -- Weapons (6E2 94, 102) ---------------------------------------------------

def test_equipment_is_a_weapon():
    assert is_weapon(_obj("HKA", 2), section="equipment")


def test_a_focus_makes_a_power_a_weapon_and_a_bare_hka_is_not_one():
    assert is_weapon(_obj("HKA", 2, mods=["FOCUS"]), section="powers")
    assert not is_weapon(_obj("HKA", 2), section="powers")


def test_a_focus_on_the_framework_reaches_its_slots():
    mp = _obj("MULTIPOWER", mods=["FOCUS"])
    assert is_weapon(_obj("RKA", 2, parent=mp), section="powers")


def _hero_with_elements(*classes):
    element = SimpleNamespace(
        xmlid="WEAPON_ELEMENT",
        assigned_adders=[SimpleNamespace(xmlid=x, display=d) for x, d in classes])
    return SimpleNamespace(maneuvers=[element])


def test_no_element_means_no_maneuvers_with_weapons():
    assert element_reach(SimpleNamespace(maneuvers=[]), ("Battle Axe",)) is Reach.NO
    hero = _hero_with_elements(("BAREHAND", "Empty Hand"))
    assert element_reach(hero, ("Battle Axe",)) is Reach.NO


def test_an_element_covers_a_weapon_its_class_names():
    hero = _hero_with_elements(("AXESMACES", "Axes, Maces, Hammers, and Picks"))
    assert element_reach(hero, ("Battle Axe",)) is Reach.YES


def test_an_element_whose_class_cannot_be_told_is_unknown():
    """'Sword' is a blade to a reader; HD says nothing that ties them."""
    hero = _hero_with_elements(("BLADES", "Blades"))
    assert element_reach(hero, ("Sword",)) is Reach.UNKNOWN
    assert element_reach(_hero_with_elements(("DEFAULTELEMENT", "Default Element")),
                         ("Sword",)) is Reach.UNKNOWN
