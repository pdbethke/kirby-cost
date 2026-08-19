"""Skill.roll_value — the roll a characteristic-based Skill prints.

    Base skill roll = 9 + (characteristic/5) or less ... standard rounding
    rules apply.                                  — 6E Volume 1, p57

The port of ``getRollValue`` was a faithful transcription of the Java, and it
still printed the wrong roll for every characteristic-based skill in the
794-file corpus, because the one thing it did NOT port was the lookup:
``_get_active_hero`` returned None unconditionally, with a comment saying
where the real lookup belonged.

That failure was invisible for a specific reason worth keeping a test for.
The no-hero fallback assumes a characteristic of 10, and ``general_level`` is
also 10, so the fallback agreed with itself and produced ``11-`` — a legal,
ordinary-looking roll for a starting character. Nothing raised, no cost moved
(costs never read the roll), and 1,858 skills printed a plausible lie.

The second bug was underneath it and could not surface until the first was
fixed: ``primary_value`` is a float ATTRIBUTE holding the last computed value,
while ``get_primary_value(hero)`` is the accessor that recomputes. The port
called ``char.primary_value()``, which is a TypeError — dead code cannot be
wrong, so it sat there through 655 green oracle runs.
"""
from __future__ import annotations

import pytest

from kirby_cost.model.rules import Rules
from kirby_cost.objects.skills.skill import Skill


class _Char:
    """Just enough characteristic to be looked up and read."""

    def __init__(self, xmlid: str, value: float):
        self.xmlid = xmlid
        self._value = value

    def get_primary_value(self, active_hero=None) -> float:
        return self._value

    def get_secondary_value(self, active_hero=None) -> float:
        return self._value


class _Hero:
    def __init__(self, char: _Char | None):
        self._char = char
        self.rules = Rules()

    def characteristic(self, _key):
        return self._char


def _skill(char_value: float, *, levels: int = 0, xmlid: str = "PRE") -> Skill:
    s = Skill()
    s._alias = "Oratory"
    s.characteristic = 7
    s._levels = levels
    s._level_value = 1.0
    s._hero = _Hero(_Char(xmlid, char_value))
    return s


# ── the formula ────────────────────────────────────────────────────────

def test_the_roll_is_nine_plus_a_fifth_of_the_characteristic():
    assert _skill(15.0).roll_value == 12


def test_a_remainder_over_a_half_rounds_up():
    """PRE 13 is 2.6 fifths. HD rounds half UP, so this is 3, not 2 — the
    difference between 12- and the 11- the broken lookup produced."""
    assert _skill(13.0).roll_value == 12


def test_a_remainder_under_a_half_rounds_down():
    assert _skill(12.0).roll_value == 11


def test_levels_bought_add_to_the_roll():
    assert _skill(15.0, levels=2).roll_value == 14


# ── the lookup ─────────────────────────────────────────────────────────

def test_the_skill_finds_its_character():
    """The regression this file exists for. Without the hero the roll falls
    back to a characteristic of 10 and prints 11- for everyone."""
    s = _skill(15.0)
    assert s._get_active_hero() is not None
    assert s.column2_output == "Oratory 12-"


def test_a_general_skill_uses_the_rules_level_not_the_object_it_found():
    """GENERAL is a sentinel. HD's second branch keys on the skill's
    `characteristic` FIELD (`== Constants.GENERAL`, which is 0), NOT on the
    xmlid of the object the lookup returned — my first version of this test
    asserted the latter and was simply wrong about HD."""
    s = _skill(15.0, xmlid="GENERAL")
    s.characteristic = 0
    assert s.roll_value == 9 + 2  # general_level 10 / 5


def test_a_general_object_on_a_normal_skill_falls_through_to_levels_alone():
    """Both of HD's first two branches can fail: the found object is GENERAL
    so branch one is skipped, and the field is not the sentinel so branch two
    is skipped. What is left adds only the levels bought — the 15 is never
    read."""
    s = _skill(15.0, levels=2, xmlid="GENERAL")
    assert s.roll_value == 9 + 2


# ── the accessor ───────────────────────────────────────────────────────

def test_primary_value_is_read_through_the_accessor_not_called():
    """`primary_value` is a float attribute. Calling it raises TypeError, and
    that is precisely what eleven call sites did across skills and talents
    until the hero lookup made them reachable. Guard the shape directly so a
    re-introduction fails here rather than eighty fixtures downstream."""
    from kirby_cost.objects.characteristics.characteristic import Characteristic

    assert not callable(Characteristic().primary_value)
    assert callable(Characteristic().get_primary_value)
