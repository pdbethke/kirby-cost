"""A Damage Classes limit measures the most one attack can reach.

Workshop spec §5.2.1, plan 1b. Peter, 2026-11-26: his players squeeze every
point, so Martial Arts and the rest of the Adding Damage rules (6E2 101-104)
figure into DCs; "in all things follow the rules and cite".

The book's worked examples are paraphrased, never quoted, with their pages.
"""
from __future__ import annotations

import pytest

from kirby_cost.builder import (
    AddedDamage as A, Kind, Limit, Pick, Problem, Purchase, Replace, Template,
    apply, buy, judge, new_build,
)
from kirby_cost.io.build_json import build_from_json, to_build_json
from kirby_cost.io.formats import load_build
from kirby_cost.template.hdt_provider import HDTTemplateProvider
from tests.corpus import require_authored_hdc

EVERY = (A.STR, A.MARTIAL, A.CSL, A.HAYMAKER, A.VELOCITY, A.DEADLY_BLOW)


@pytest.fixture(scope="module")
def provider():
    return HDTTemplateProvider()


def DC(n, adders, doubling=False):
    return Limit(Limit.Kind.DAMAGE_CLASSES, n, None, (), doubling, adders)


def _empty(provider):
    return new_build(Template.SUPERHEROIC, template_provider=provider, name="Test NPC",
                     base_points=400, disad_points=0, experience=0)


def _with(doc, provider, *purchases):
    for p in purchases:
        doc = apply(doc, [buy(doc, p, template=provider)])
    return doc


def _str(doc, total):
    (row,) = [c for c in doc["characteristics"] if c["xmlid"] == "STR"]
    return apply(doc, [Replace(row["id"], {**row, "levels": total - 10})])


def _power(xmlid, levels, *mods, name=""):
    return Purchase(Kind.POWER, xmlid, levels, name, None, (), tuple(mods))


def _maneuver(hd_id, display, dc, effect, add_str=True, use_weapon=False):
    return {"id": hd_id, "xmlid": "MANEUVER", "base_cost": 4.0, "alias": display,
            "maneuver": True, "category": "Hand To Hand", "display": display,
            "ocv": "+0", "dcv": "+2", "dc": dc, "phase": "1/2", "effect": effect,
            "add_str": add_str, "maneuver_active_cost": 20, "damage_type": 0,
            "max_str": 0, "str_multiplier": 1, "use_weapon": use_weapon,
            "weapon_effect": "Weapon [WEAPONDC] Strike"}


MARTIAL_STRIKE = _maneuver("9000000000001", "Martial Strike", 2, "[NORMALDC] Strike")
EXTRA_2 = {"id": "9000000000002", "xmlid": "EXTRADC", "levels": 2,
           "alias": "+2 HTH Damage Class(es)"}


def _martial(doc, *rows):
    return {**doc, "martial_arts": [*doc["martial_arts"], *rows]}


def _problems(doc, provider, limit, kind=Problem.Kind.OVER_LIMIT):
    return {p.hd_id: p.detail for p in judge(doc, limits=(limit,),
                                             template_provider=provider).problems
            if p.kind is kind}


# -- STR is an attack ---------------------------------------------------------

def test_str_is_a_damage_class_per_five(provider):
    """6E1 137: 1d6 per 5 STR. STR 50 punches for 10 DCs."""
    doc = _str(_empty(provider), 50)
    assert _problems(doc, provider, DC(9, ()))[None] \
        == "Damage Classes 10; the limit is 9"


# -- Haymaker (6E2 58, 71; Peter: HTH only) -------------------------------------

def test_a_haymaker_adds_four_to_a_punch(provider):
    doc = _empty(provider)                                   # STR 10: 2 DCs
    assert _problems(doc, provider, DC(5, (A.HAYMAKER,)))[None] \
        == "Damage Classes 6 (Haymaker with STR: STR 2 + Haymaker 4); the limit is 5"


def test_a_haymaker_is_hth_and_never_a_ranged_attack(provider):
    doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 8))
    blast = doc["powers"][0]["id"]
    assert build_from_json(doc).powers[0].range_value > 0
    assert blast not in _problems(doc, provider, DC(8, (A.HAYMAKER,)))


def test_one_maneuver_an_attack(provider):
    """6E2 71: a Haymaker cannot be combined with another maneuver. With a
    Martial Strike too, the best is the Haymaker's +4, not +4 and +2."""
    doc = _martial(_empty(provider), MARTIAL_STRIKE)
    assert _problems(doc, provider, DC(5, (A.HAYMAKER, A.MARTIAL)))[None].startswith(
        "Damage Classes 6 (Haymaker with STR")


# -- Doubling (6E2 101) ---------------------------------------------------------

def test_doubling_caps_the_stack_at_twice_the_base(provider):
    doc = _empty(provider)                                   # 2 + 4 = 6, doubled cap 4
    assert _problems(doc, provider, DC(3, (A.HAYMAKER,), doubling=True))[None] \
        == "Damage Classes 4 (Haymaker with STR: STR 2 + Haymaker 4); the limit is 3"
    assert None not in _problems(doc, provider, DC(4, (A.HAYMAKER,), doubling=True))


def test_a_great_str_cannot_more_than_double_a_small_killing_attack(provider):
    """6E2 101's Matterhorn: a cheap killing weapon in a strong hand doubles,
    and no more. HKA 1d6 (3 DCs) with STR 60 (+12) is held to 6."""
    doc = _with(_str(_empty(provider), 60), provider, _power("HKA", 1))
    hka = doc["powers"][0]["id"]
    assert _problems(doc, provider, DC(5, (A.STR,), doubling=True))[hka] \
        == "Damage Classes 6 (HKA: base 3 + STR 12); the limit is 5"


# -- Martial Arts (6E2 94, 101-102) ---------------------------------------------

def test_a_martial_strike_adds_to_str(provider):
    doc = _martial(_empty(provider), MARTIAL_STRIKE)        # STR 10: 2 + 2
    assert _problems(doc, provider, DC(3, (A.MARTIAL,)))[None] \
        == "Damage Classes 4 (Martial Strike with STR: STR 2 + Martial Strike 2); the limit is 3"


def test_a_maneuver_that_does_not_add_str_is_its_own_dcs(provider):
    """HD's ADDSTR says whether a maneuver's damage is STR plus its DCs
    (`Maneuver.total_dc` adds STR only then). One that does not is its DCs
    alone: 4, not STR 2 + 4."""
    blow = _maneuver("9000000000004", "Set Blow", 4, "[NORMALDC] Strike", add_str=False)
    doc = _martial(_empty(provider), blow)
    assert _problems(doc, provider, DC(3, (A.MARTIAL,)))[None] \
        == "Damage Classes 4 (Set Blow with STR: Set Blow 4); the limit is 3"


def test_martial_arts_do_not_count_unless_the_gm_counts_them(provider):
    doc = _martial(_empty(provider), MARTIAL_STRIKE)
    assert None not in _problems(doc, provider, DC(2, ()))


def test_extra_dcs_add_to_every_maneuver(provider):
    """6E2 94. Ravel's Joint Lock/Throw (an NND, an attack of its own) goes
    from 2 to 4; a Martial Strike on his STR 10 from 4 to 6."""
    ravel = to_build_json(load_build(str(require_authored_hdc("Ravel")), format="hdc"))
    doc = _martial(ravel, MARTIAL_STRIKE, EXTRA_2)
    found = _problems(doc, provider, DC(3, (A.MARTIAL,)))
    assert found[None] == ("Damage Classes 6 (Martial Strike with STR: STR 2 + "
                           "Martial Strike 2 + Extra DCs 2); the limit is 3")
    assert found["1648502990626"] == "Damage Classes 4; the limit is 3"


def test_ravels_grappling_block_is_not_an_attack(provider):
    ravel = to_build_json(load_build(str(require_authored_hdc("Ravel")), format="hdc"))
    assert "1648370660426" not in _problems(ravel, provider, DC(0, EVERY))


def test_str_then_the_maneuver_on_an_hka_never_str_twice(provider):
    """6E2 102 (Chan Hseng): the HKA is the base, STR adds, then the
    maneuver's bonus; STR is not added to the maneuver first. HKA 1d6 (3),
    STR 15 (+3), Martial Strike (+2) is 8, not 11."""
    doc = _martial(_with(_str(_empty(provider), 15), provider, _power("HKA", 1)),
                   MARTIAL_STRIKE)
    hka = doc["powers"][0]["id"]
    assert _problems(doc, provider, DC(7, (A.STR, A.MARTIAL)))[hka] == (
        "Damage Classes 8 (Martial Strike with HKA: base 3 + STR 3 + Martial Strike 2); "
        "the limit is 7")


def test_a_killing_or_nnd_maneuver_adds_nothing_to_a_weapon(provider):
    """6E2 101: a maneuver that changes the damage type differentiates; it
    does not add."""
    nerve = _maneuver("9000000000003", "Nerve Strike", 2, "[NNDDC]", add_str=False)
    doc = _martial(_with(_empty(provider), provider, _power("HKA", 1)), nerve)
    hka = doc["powers"][0]["id"]
    assert hka not in _problems(doc, provider, DC(3, (A.MARTIAL,)))


def test_maneuvers_reach_a_weapon_only_through_a_weapon_element(provider):
    """6E2 94. A Battle Axe bought as equipment takes no Martial Strike
    without an Element for axes."""
    doc = _martial(_with(_empty(provider), provider,
                         Purchase(Kind.EQUIPMENT, "HKA", 1, "Battle Axe", None, (), ())),
                   MARTIAL_STRIKE)
    axe = doc["equipment"][0]["id"]
    assert axe not in _problems(doc, provider, DC(3, (A.MARTIAL,)))


# -- Velocity (6E2 58, 72, 101-102) ------------------------------------------------

def test_the_books_move_through(provider):
    """6E2 102: Flight 30m, STR 20, a Move Through does 9d6 -- 4 from STR,
    5 from velocity. That is at Combat speed: with no Noncombat movement
    the flier is held to it."""
    doc = _with(_str(_empty(provider), 20), provider,
                _power("FLIGHT", 30, Pick("NONONCOMBAT", 0, None)))
    assert _problems(doc, provider, DC(8, (A.VELOCITY,)))[None] == (
        "Damage Classes 9 (Move Through with STR: STR 4 + v/6 5); the limit is 8")


def test_a_move_through_may_run_at_noncombat_speed(provider):
    """6E2 72: at Noncombat 60m the same flier does 4 + 10."""
    doc = _with(_str(_empty(provider), 20), provider, _power("FLIGHT", 30))
    assert _problems(doc, provider, DC(8, (A.VELOCITY,)))[None].startswith(
        "Damage Classes 14 (Move Through with STR")


# -- Combat Skill Levels (6E2 101; 6E1 72) -------------------------------------

def _csl(option, levels, name=""):
    return Purchase(Kind.SKILL, "COMBAT_LEVELS", levels, name, option, (), ())


def test_two_csls_are_a_damage_class(provider):
    doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 8), _csl("ALL", 4))
    blast = doc["powers"][0]["id"]
    assert _problems(doc, provider, DC(9, (A.CSL,)))[blast] \
        == "Damage Classes 10 (ENERGYBLAST: base 8 + CSLs 2); the limit is 9"


def test_a_csl_that_names_nothing_on_the_build_is_reported_not_guessed(provider):
    doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 8),
                _csl("SINGLE", 2, name="+2 with my lucky right hook"))
    (csl_id,) = [s["id"] for s in doc["skills"] if s["xmlid"] == "COMBAT_LEVELS"]
    unmeasured = _problems(doc, provider, DC(20, (A.CSL,)), Problem.Kind.UNMEASURED)
    assert "name no attack" in unmeasured[csl_id]
    assert not _problems(doc, provider, DC(20, ()), Problem.Kind.UNMEASURED)


# -- Peter's characters ---------------------------------------------------------

@pytest.mark.parametrize("name", ["Ravel", "Bokor", "PowerLad"])
def test_every_authored_character_is_measured_with_every_method(name, provider):
    doc = to_build_json(load_build(str(require_authored_hdc(name)), format="hdc"))
    verdict = judge(doc, limits=(DC(0, EVERY, doubling=True),), template_provider=provider)
    assert [p for p in verdict.problems if p.kind is Problem.Kind.OVER_LIMIT]


# -- What a maneuver or STR can add to (6E2 71, 101) ---------------------------

def test_a_haymaker_adds_to_damage_not_to_a_transform(provider):
    """6E2 71: a Haymaker adds to the damage of a Normal or Killing Damage
    attack. A HTH Transform is neither."""
    doc = _with(_empty(provider), provider,
                _power("TRANSFORM", 4, Pick("NORANGE", 0, None)))
    drain = doc["powers"][0]["id"]
    hero = build_from_json(doc)
    assert hero.powers[0].range_value == 0 and hero.powers[0].does_damage
    assert drain not in _problems(doc, provider, DC(4, (A.HAYMAKER, A.MARTIAL)))


def test_an_unlimited_str_power_stacks_on_str_once(provider):
    """STR 10 plus a +20 STR power is a 30 STR punch: 6 DCs, its STR
    counted once though HD's primary figure already carries it."""
    doc = _with(_empty(provider), provider, _power("STR", 20, name="Pump Up"))
    pump = doc["powers"][0]["id"]
    assert _problems(doc, provider, DC(5, ()))[pump] == "Damage Classes 6; the limit is 5"


def test_a_limited_str_power_is_reported_not_stacked(provider):
    doc = _with(_empty(provider), provider,
                _power("STR", 20, Pick("LIMITEDPOWER", 0, None), name="Lift Only"))
    pump = doc["powers"][0]["id"]
    unmeasured = _problems(doc, provider, DC(50, ()), Problem.Kind.UNMEASURED)
    assert "Limited Power" in unmeasured[pump]
