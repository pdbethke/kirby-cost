"""Damage Classes: counting them, turning them back into dice, adding them.

6E2 p.99's Damage Class Table: a Normal Damage DC is 1d6; a Killing Damage
DC is 5 Active Points, so 3 DC buy 1d6 and the steps between are +1 and
1/2d6 (1 DC = +1, 2 DC = 1/2d6, 3 DC = 1d6, 4 DC = 1d6+1, 5 DC = 1 1/2d6).
6E2 p.101: added damage comes in whole DCs, "regardless of the type of
damage done".

The defect these replace: `augment_with_str` counted Killing damage in
half-die steps, one step per DC, so STR 5 on a 1d6 HKA gave 1 1/2d6 where the
book gives 1d6+1, and the +1 pip of a 1d6+1 knife was dropped.
"""
import pytest

from kirby_cost.engine.damage import (
    KILLING, NORMAL, Dice, add_damage_classes, augment_with_str,
    damage_classes, dice_for,
)


def d(full, half=False, plus_one=False, minus_one=False):
    return Dice(full=full, half=half, plus_one=plus_one, minus_one=minus_one)


# ── the Killing column of 6E2 p.99 ──────────────────────────────────────────

KILLING_LADDER = [
    (1, d(0, plus_one=True)),
    (2, d(0, half=True)),
    (3, d(1)),
    (4, d(1, plus_one=True)),
    (5, d(1, half=True)),
    (6, d(2)),
    (7, d(2, plus_one=True)),
    (8, d(2, half=True)),
    (9, d(3)),
]


@pytest.mark.parametrize("dcs,dice", KILLING_LADDER)
def test_killing_dcs_become_the_table_s_dice(dcs, dice):
    assert dice_for(dcs, KILLING) == dice


@pytest.mark.parametrize("dcs,dice", KILLING_LADDER)
def test_killing_dice_count_back_to_their_dcs(dcs, dice):
    assert damage_classes(dice, KILLING) == dcs


def test_the_minus_one_rung_is_the_same_dc_as_the_half_die():
    """HD's MINUSONEPIP ("+1d6 -1") is bought at the half-die's price: the
    Colt Peacemaker's 2d6-1 RKA is 5 DC, as 1 1/2d6 is."""
    assert damage_classes(d(2, minus_one=True), KILLING) == 5


def test_normal_damage_is_a_die_per_dc():
    assert dice_for(5, NORMAL) == d(5)
    assert damage_classes(d(5), NORMAL) == 5
    # A half die on Normal Damage is not a Damage Class (6E2 p.101: there is
    # no such thing as half a DC).
    assert damage_classes(d(3, half=True), NORMAL) == 3


def test_a_negative_dc_count_is_refused():
    with pytest.raises(ValueError):
        dice_for(-1, KILLING)


def test_an_unknown_damage_type_is_refused():
    """No silent fallback to Normal for a type this table doesn't cover."""
    with pytest.raises(ValueError):
        dice_for(3, "nnd")
    with pytest.raises(ValueError):
        damage_classes(d(3), "nnd")


# ── 6E2 p.101's worked example ──────────────────────────────────────────────

def test_a_martial_strike_takes_a_3d6_club_to_5d6():
    assert add_damage_classes(d(3), NORMAL, 2) == d(5)


def test_a_martial_strike_takes_a_1d6_hka_sword_to_one_and_a_half_d6():
    assert add_damage_classes(d(1), KILLING, 2) == d(1, half=True)


def test_adding_keeps_a_normal_attack_s_half_die():
    assert add_damage_classes(d(3, half=True), NORMAL, 2) == d(5, half=True)


def test_adding_nothing_changes_nothing():
    assert add_damage_classes(d(1, plus_one=True), KILLING, 0) == d(1, plus_one=True)


# ── STR on a Killing attack (6E1 p.137, 6E2 p.99) ──────────────────────────

@pytest.mark.parametrize("strength,expected", [
    (0, d(1)),
    (4, d(1)),
    (5, d(1, plus_one=True)),      # 4 DC; was 1 1/2d6
    (10, d(1, half=True)),         # 5 DC; was 2d6
    (15, d(2)),                    # 6 DC
    (20, d(2)),                    # the Doubling Rule caps at 3 more DC
])
def test_str_on_a_1d6_hka(strength, expected):
    assert augment_with_str(d(1), KILLING, strength) == expected


def test_str_keeps_a_killing_attack_s_plus_one():
    """A 1d6+1 knife (4 DC) with STR 10 is 6 DC: 2d6. The old helper had no
    way to hear about the +1."""
    assert augment_with_str(d(1, plus_one=True), KILLING, 10) == d(2)


@pytest.mark.parametrize("strength,expected", [
    (0, d(4)), (10, d(6)), (20, d(8)), (40, d(8)),
])
def test_str_on_a_normal_attack_doubles_at_most(strength, expected):
    assert augment_with_str(d(4), NORMAL, strength) == expected


def test_str_on_another_damage_type_is_refused():
    with pytest.raises(ValueError):
        augment_with_str(d(2), "nnd", 15)
