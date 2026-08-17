"""Class defaults must encode the 6E rules, with no template present.

The engine's floor is that it supplies the non-disputable 6E defaults and the
template supplies only the catalogue and per-object overrides. Nothing tested
that floor until now: all 655 oracle fixtures load through
a template provider, so every class default is overwritten by
``apply_template`` before a cost is ever computed. A wrong default is therefore
invisible to the entire suite.

That is not hypothetical. ``Running`` charged 2 CP/m and ``Swimming`` 1 CP/m --
both 5E values -- masked by the template supplying the correct 6E ones. A
consumer that costs an object with no template in hand gets the class default,
and nothing else would have caught it being wrong.

These tests instantiate the classes directly and assert against the rulebook,
quoted below. No template, no provider, no HDC file.
"""
import pytest

from kirby_cost.objects.characteristics.leaping import Leaping
from kirby_cost.objects.characteristics.running import Running
from kirby_cost.objects.characteristics.swimming import Swimming


# HERO System 6th Edition Volume 1, p43:
#
#   "All characters can Run up to 12m in a Phase, Swim up to 4m, and Leap up
#    to 4m forward."
#
#   Movement Mode | Base value | Cost
#   Running       | 12m        | 1 Character Point per +1m
#   Swimming      |  4m        | 1 Character Point per +2m
#   Leaping       |  4m        | 1 Character Point per +2m
#
# Expressed as cost-per-metre so the assertion does not depend on how a given
# class splits the ratio between _level_cost and _level_value.
MOVEMENT_COST_PER_METRE = {
    Running: (1.0, "6E1 p43: Running, 1 Character Point per +1m"),
    Swimming: (0.5, "6E1 p43: Swimming, 1 Character Point per +2m"),
    Leaping: (0.5, "6E1 p43: Leaping, 1 Character Point per +2m"),
}


@pytest.mark.parametrize(
    "cls,expected,citation",
    [(c, e, s) for c, (e, s) in MOVEMENT_COST_PER_METRE.items()],
    ids=lambda v: v.__name__ if isinstance(v, type) else "",
)
def test_movement_class_default_matches_the_rulebook(cls, expected, citation):
    """A freshly constructed movement characteristic costs the 6E rate."""
    obj = cls()
    level_cost = obj._level_cost
    level_value = obj._level_value

    assert level_value, f"{cls.__name__}: _level_value must be non-zero ({citation})"
    actual = level_cost / level_value

    assert actual == expected, (
        f"{cls.__name__} class default is {level_cost} CP per {level_value}m "
        f"= {actual} CP/m, but {citation} (= {expected} CP/m). "
        "This default is normally masked by the loaded template; it becomes "
        "live wherever an object is costed without one."
    )


def test_movement_base_values_match_the_rulebook():
    """6E1 p43: Running 12m, Swimming 4m, Leaping 4m.

    Guards the other half of the same table. Leaping derives its base value
    from STR rather than carrying a flat one, so it is checked separately
    where that calculation lives -- this covers the two flat ones.
    """
    import os

    from kirby_cost.template.hdt_provider import HDTTemplateProvider

    if not os.environ.get(HDTTemplateProvider.ENV_VAR):
        pytest.skip(f"no template configured ({HDTTemplateProvider.ENV_VAR})")

    provider = HDTTemplateProvider()
    expected = {"RUNNING": 12, "SWIMMING": 4}
    for xmlid, base in expected.items():
        tmpl = provider.get_template_data(xmlid)
        assert tmpl is not None, f"{xmlid} is missing from the template"
        assert tmpl.base_value == base, (
            f"{xmlid} base_value is {tmpl.base_value}, 6E1 p43 says {base}m"
        )


# ── Skill-family defaults ────────────────────────────────────────────────
#
# The generic Skill default of 2 CP per +1 is CORRECT and confirmed by the
# master skills table (6E1 p63: most Skills are "3/2" -- base 3, +1 costs 2).
# But two families cost 1 CP per +1 and inherited the generic 2.0 anyway.
# Knowledge Skill already sets 1.0; these were its missed neighbours.

def test_professional_skill_level_cost():
    """6E1 p88: '2 character points for an 11- roll ... +1 to roll per +1 point'."""
    from kirby_cost.objects.skills.professional_skill import ProfessionalSkill

    o = ProfessionalSkill()
    assert o._level_cost == 1.0, (
        f"ProfessionalSkill._level_cost is {o._level_cost}; 6E1 p88 says +1 to "
        "roll costs +1 point. 2.0 is the generic Skill rate, inherited by "
        "mistake -- Background Skills cost 1 CP per +1."
    )


def test_mental_combat_skill_level_cost():
    """6E1 p73: 'For 1 Character Point, a character can buy +1 ...' (MCSLs)."""
    from kirby_cost.objects.skills.mental_combat_levels import MentalCombatLevels

    o = MentalCombatLevels()
    assert o._level_cost == 1.0, (
        f"MentalCombatLevels._level_cost is {o._level_cost}; 6E1 p73 says 1 "
        "Character Point per +1."
    )


def test_resource_pool_perk_rate():
    """APG p194 table: 'Equipment Points: 1 Character Point for 5 Equipment Points.'

    The class had level_cost=5.0 / level_value=1.0 -- the two transposed,
    charging 5 CP per point instead of 1 CP per 5 points. A 25x overcharge.

    The rate varies by category (Vehicle/Base and Follower/Contact are 1 CP
    for 2), so the class default is the Equipment Points rate -- the most
    common category per APG p196 -- and the template supplies the others.
    """
    from kirby_cost.objects.perks.resource_pool import ResourcePool

    o = ResourcePool()
    assert o._level_value, "ResourcePool._level_value must be non-zero"
    cp_per_point = o._level_cost / o._level_value
    assert cp_per_point == 0.2, (
        f"ResourcePool is {o._level_cost} CP per {o._level_value} points "
        f"= {cp_per_point} CP/point; APG p194 says 1 Character Point for 5 "
        "Equipment Points (= 0.2 CP/point)."
    )
