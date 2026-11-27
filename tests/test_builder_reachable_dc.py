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
    from 2 to 4; a Martial Strike from 10 to 12, on his STR 10 with
    Reinforced String's +30 (an unlimited STR slot) on: STR 40."""
    ravel = to_build_json(load_build(str(require_authored_hdc("Ravel")), format="hdc"))
    doc = _martial(ravel, MARTIAL_STRIKE, EXTRA_2)
    found = _problems(doc, provider, DC(3, (A.MARTIAL,)))
    assert found[None] == ("Damage Classes 12 (Martial Strike with STR: STR 8 + "
                           "Martial Strike 2 + Extra DCs 2; Maleable Sting Body 45: "
                           "Reinforced String 30); the limit is 3")
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


# -- A framework's points (6E1 401, 404-405, 410, 411, 413) ---------------------

def _framework(doc, row, *, fixed):
    """Everything bought so far as slots of ``row`` (Fixed or Variable)."""
    slots = [{**r, "parent": row["id"], **({} if fixed else {"ultra_slot": False})}
             for r in doc["powers"]]
    return {**doc, "powers": [row, *slots]}


def _multipower(doc, reserve, *, fixed):
    return _framework(doc, {"id": "20", "xmlid": "MULTIPOWER", "base_cost": float(reserve),
                            "min_cost": 1.0, "max_cost": 9999.0, "alias": "Multipower",
                            "name": "Tricks"}, fixed=fixed)


def _fists_and_flight(provider, *, fixed):
    """A 60 reserve: Fists (HA 12d6, 60 Active Points) and Zoom (Flight
    60m, 60), STR 10, Running 12m (24m Noncombat: v/6 4 with no slot)."""
    doc = _with(_empty(provider), provider, _power("HANDTOHANDATTACK", 12, name="Fists"),
                _power("FLIGHT", 60, name="Zoom"))
    return _multipower(doc, 60, fixed=fixed)


def test_slots_of_one_multipower_stack_only_as_far_as_its_reserve(provider):
    """6E1 405-406: Variable slots split the reserve; the points are
    allocated once a Phase (6E1 410), so a Move Through's velocity and its
    attack share them. Each Flight point is 2m Noncombat, a DC per 3; each
    die of Fists 5 points, so the least of Fists rides the most of Zoom:
    1d6 (5) + STR 2 + 108m / 6, 54m being the least Flight that buys the
    18. Both full would be 14 + 20."""
    doc = _fists_and_flight(provider, fixed=False)
    fists = doc["powers"][1]["id"]
    assert _problems(doc, provider, DC(20, (A.VELOCITY,)))[fists] == (
        "Damage Classes 21 (Move Through with Fists: base 3 + v/6 18; "
        "Tricks 60: Fists 5 + Zoom 54); the limit is 20")


def test_a_fixed_slot_never_gives_up_points(provider):
    """6E1 404: a Fixed slot takes its full Active Points. Fists fills the
    reserve, so Zoom is never on beside it; he runs instead."""
    doc = _fists_and_flight(provider, fixed=True)
    fists = doc["powers"][1]["id"]
    assert _problems(doc, provider, DC(17, (A.VELOCITY,)))[fists] == (
        "Damage Classes 18 (Move Through with Fists: base 14 + v/6 4); the limit is 17")


def test_powerlads_rending_cannot_borrow_his_leap_from_brick_tricks(provider):
    """Rending and Tearing (HKA) and Iron Grasshopper (the Leaping that
    makes his 140m a Phase) are Fixed slots of one 45 reserve. Without the
    leap his best is his Running, 16m Noncombat: 9 + STR 8 + 2. His bare
    STR can still ride the leap."""
    doc = to_build_json(load_build(str(require_authored_hdc("PowerLad")), format="hdc"))
    found = _problems(doc, provider, DC(16, (A.STR, A.VELOCITY)))
    assert found["1727271627360"] == (
        "Damage Classes 19 (Move Through with Rending and Tearing: base 9 + STR 8 + v/6 2); "
        "the limit is 16")
    assert found[None] == (
        "Damage Classes 31 (Move Through with STR: STR 8 + v/6 23; "
        "Brick Tricks 45: Iron Grasshopper 44); the limit is 16")


def test_ravels_armaments_move_through_on_the_form_outside_his_multipower(provider):
    """String Slide (26m) is a Fixed 45 slot beside "ARMaments" in a 45
    reserve; Floating String Form (12m, no Noncombat) is in no framework."""
    doc = to_build_json(load_build(str(require_authored_hdc("Ravel")), format="hdc"))
    assert _problems(doc, provider, DC(12, (A.VELOCITY,)))["1648351359965"] == (
        'Damage Classes 13 (Move Through with "ARMaments" : base 11 + v/6 2); '
        "the limit is 12")


def test_a_vpp_is_measured_as_written_and_reported(provider):
    """6E1 411: a VPP can build any power up to its Control Cost, so the
    slots it holds now are not the most it can reach."""
    doc = _with(_empty(provider), provider, _power("HANDTOHANDATTACK", 6, name="Fists"))
    doc = _framework(doc, {"id": "20", "xmlid": "VPP", "levels": 30,
                           "alias": "Variable Power Pool", "name": "Gadgets",
                           "adders": [{"xmlid": "CONTROLCOST", "levels": 30,
                                       "level_cost": 1.0, "level_value": 2.0}]},
                     fixed=True)
    assert _problems(doc, provider, DC(7, ()))[doc["powers"][1]["id"]] == (
        "Damage Classes 8; the limit is 7")
    unmeasured = _problems(doc, provider, DC(20, ()), Problem.Kind.UNMEASURED)
    assert "Control Cost" in unmeasured["20"]


def test_str_from_a_slot_is_there_only_while_the_slot_is_on(provider):
    """A +20 STR slot that HD folds into the primary STR shares a 30 reserve
    with an HKA 2d6 (30): both Fixed, so the knife gets STR 10 (2 DCs), not
    30. Bare STR still has the slot: 30 STR, 6 DCs."""
    def doc_with(reserve):
        doc = _with(_empty(provider), provider, _power("HKA", 2, name="Knife"),
                    _power("STR", 20, name="Pump Up"))
        doc = {**doc, "powers": [{**r, "affects_primary": True, "affects_total": True}
                                 if r["xmlid"] == "STR" else r for r in doc["powers"]]}
        return _multipower(doc, reserve, fixed=True)
    doc, roomy = doc_with(30), doc_with(50)
    knife = doc["powers"][1]["id"]
    found = _problems(doc, provider, DC(5, (A.STR,)))
    assert found[knife] == "Damage Classes 8 (Knife: base 6 + STR 2); the limit is 5"
    assert found[None] == "Damage Classes 6 (STR: STR 6; Tricks 30: Pump Up 20); the limit is 5"
    assert _problems(roomy, provider, DC(5, (A.STR,)))[roomy["powers"][1]["id"]] == (
        "Damage Classes 12 (Knife: base 6 + STR 6; Tricks 50: Knife 30 + Pump Up 20); "
        "the limit is 5")


def test_skill_levels_in_a_slot_count_only_while_they_fit(provider):
    """Skill Levels bought as a slot are on or off (6E1 405); a 40 reserve
    holds the Blast 8d6 (40) or the levels, not both."""
    def doc_with(reserve):
        doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 8, name="Bolt"),
                    _csl("ALL", 4))
        csl = {**doc["skills"][0]}
        doc = {**doc, "skills": [], "powers": [*doc["powers"], csl]}
        return _multipower(doc, reserve, fixed=True)
    tight, roomy = doc_with(40), doc_with(80)
    bolt = tight["powers"][1]["id"]
    assert _problems(tight, provider, DC(7, (A.CSL,)))[bolt] == "Damage Classes 8; the limit is 7"
    assert _problems(roomy, provider, DC(7, (A.CSL,)))[bolt].startswith(
        "Damage Classes 10 (Bolt: base 8 + CSLs 2; Tricks 80: Bolt 40 + ")


# -- Deadly Blow (6E1 115) -------------------------------------------------------

def _knife(provider, talent_name):
    """A 2d6 HKA in an Obvious Accessible Focus (a weapon, 6E2 94) and one
    level of Deadly Blow."""
    doc = _with(_empty(provider), provider,
                _power("HKA", 2, Pick("FOCUS", 0, "OAF"), name="Knife"),
                Purchase(Kind.TALENT, "DEADLYBLOW", 1, talent_name, None, (), ()))
    return doc


def test_deadly_blow_adds_three_a_level_to_a_killing_weapon(provider):
    doc = _knife(provider, "Deadly Blow: HKA")
    knife = doc["powers"][0]["id"]
    assert _problems(doc, provider, DC(8, (A.DEADLY_BLOW,)))[knife] == (
        "Damage Classes 9 (Knife: base 6 + Deadly Blow 3); the limit is 8")
    assert knife not in _problems(doc, provider, DC(8, ()))


def test_a_deadly_blow_that_names_neither_hka_nor_rka_is_reported(provider):
    doc = _knife(provider, "Deadly Blow")
    (talent,) = [t["id"] for t in doc["talents"]]
    unmeasured = _problems(doc, provider, DC(20, (A.DEADLY_BLOW,)), Problem.Kind.UNMEASURED)
    assert "HKAs or RKAs" in unmeasured[talent]


def test_deadly_blow_in_a_slot_counts_only_while_it_fits(provider):
    """Bought as a slot, it is on or off (6E1 405): a 30 reserve holds the
    Knife (30) and nothing else; a 40 one holds both."""
    def doc_with(reserve):
        doc = _knife(provider, "Deadly Blow: HKA")
        doc = {**doc, "talents": [], "powers": [*doc["powers"], *doc["talents"]]}
        return _multipower(doc, reserve, fixed=True)
    tight, roomy = doc_with(30), doc_with(40)
    knife = tight["powers"][1]["id"]
    assert _problems(tight, provider, DC(5, (A.DEADLY_BLOW,)))[knife] == (
        "Damage Classes 6; the limit is 5")
    assert _problems(roomy, provider, DC(5, (A.DEADLY_BLOW,)))[knife].startswith(
        "Damage Classes 9 (Knife: base 6 + Deadly Blow 3; Tricks 40: Knife 30 + ")


def test_deadly_blow_bought_for_hkas_adds_nothing_to_an_rka(provider):
    """6E1 115: bought for HKAs or RKAs; both means buying it twice."""
    doc = _with(_empty(provider), provider,
                _power("RKA", 2, Pick("FOCUS", 0, "OAF"), name="Pistol"),
                Purchase(Kind.TALENT, "DEADLYBLOW", 1, "Deadly Blow: HKA", None, (), ()))
    pistol = doc["powers"][0]["id"]
    assert pistol not in _problems(doc, provider, DC(6, (A.DEADLY_BLOW,)))


def test_deadly_blow_needs_a_weapon_not_a_bare_killing_attack(provider):
    """6E1 115: "Killing Attacks involving weapons". Claws bought as an HKA
    with no Focus are not one (6E2 94, R12)."""
    doc = _with(_empty(provider), provider, _power("HKA", 2, name="Claws"),
                Purchase(Kind.TALENT, "DEADLYBLOW", 1, "Deadly Blow: HKA", None, (), ()))
    claws = doc["powers"][0]["id"]
    assert claws not in _problems(doc, provider, DC(6, (A.DEADLY_BLOW,)))


def test_a_deadly_blow_for_normal_damage_weapons_is_reported(provider):
    """6E1 115 lets a character define it for Normal Damage weapons
    instead; which ones is in its words."""
    doc = _knife(provider, "Deadly Blow: HKA, Normal Damage weapons")
    (talent,) = [t["id"] for t in doc["talents"]]
    unmeasured = _problems(doc, provider, DC(20, (A.DEADLY_BLOW,)), Problem.Kind.UNMEASURED)
    assert "Normal Damage" in unmeasured[talent]


# -- Two or more slots on at once (6E1 404-406) -----------------------------------

def _folded(doc):
    """Rows marked as HD marks a power that raises its characteristic."""
    return {**doc, "powers": [{**r, "affects_primary": True, "affects_total": True}
                              for r in doc["powers"]]}


def test_every_slot_feeding_one_total_can_be_on_while_the_reserve_holds(provider):
    """6E1 404: no number limit on slots on at once, only the reserve's
    Active Points. Two +10m Running slots (10 each) beside his own 12m:
    32m, 64m Noncombat, v/6 10, in a 20 reserve; in a 19 one, only one is
    on: 22m, 44m, v/6 7."""
    def doc_with(reserve):
        doc = _with(_empty(provider), provider, _power("RUNNING", 10, name="Sprint"),
                    _power("RUNNING", 10, name="Dash"))
        return _multipower(_folded(doc), reserve, fixed=True)
    assert _problems(doc_with(20), provider, DC(5, (A.VELOCITY,)))[None] == (
        "Damage Classes 12 (Move Through with STR: STR 2 + v/6 10; "
        "Tricks 20: Sprint 10 + Dash 10); the limit is 5")
    assert _problems(doc_with(19), provider, DC(5, (A.VELOCITY,)))[None] == (
        "Damage Classes 9 (Move Through with STR: STR 2 + v/6 7; Tricks 19: Dash 10); "
        "the limit is 5")


def test_every_str_slot_adds_while_the_reserve_holds_it(provider):
    """Two +20 STR slots (20 each), whether or not HD folds them into the
    primary figure: STR 50, 10 DCs, in a 40 reserve; one in a 39 one."""
    for fold in (True, False):
        def doc_with(reserve):
            doc = _with(_empty(provider), provider, _power("STR", 20, name="Pump Up"),
                        _power("STR", 20, name="Bulk Up"))
            return _multipower(_folded(doc) if fold else doc, reserve, fixed=True)
        assert _problems(doc_with(40), provider, DC(5, ()))[None] == (
            "Damage Classes 10 (STR: STR 10; Tricks 40: Pump Up 20 + Bulk Up 20); "
            "the limit is 5"), fold
        assert _problems(doc_with(39), provider, DC(5, ()))[None] == (
            "Damage Classes 6 (STR: STR 6; Tricks 39: Bulk Up 20); the limit is 5"), fold


def test_a_str_slot_adds_to_a_killing_attack_beside_it(provider):
    """6E2 101: STR adds to an HKA, whatever bought it. Knife (30) and a
    +20 STR slot HD does not fold into the primary figure (20) in a 50
    reserve: 6 + STR 30's 6."""
    doc = _with(_empty(provider), provider, _power("HKA", 2, name="Knife"),
                _power("STR", 20, name="Pump Up"))
    doc = _multipower(doc, 50, fixed=True)
    assert _problems(doc, provider, DC(5, (A.STR,)))[doc["powers"][1]["id"]] == (
        "Damage Classes 12 (Knife: base 6 + STR 6; Tricks 50: Knife 30 + Pump Up 20); "
        "the limit is 5")


def test_a_str_power_hd_keeps_off_the_primary_figure_is_still_str(provider):
    """6E2 101: STR adds to an HKA whatever bought it. A +20 STR power in no
    framework that HD does not fold into primary STR: STR 30 under the
    Knife (6 + 6), and the power's own punch is that STR, counted once."""
    doc = _with(_empty(provider), provider, _power("HKA", 2, name="Knife"),
                _power("STR", 20, name="Pump Up"))
    doc = {**doc, "powers": [{**r, "affects_primary": False, "affects_total": False}
                             if r["xmlid"] == "STR" else r for r in doc["powers"]]}
    knife, pump = doc["powers"][0]["id"], doc["powers"][1]["id"]
    found = _problems(doc, provider, DC(5, (A.STR,)))
    assert found[knife] == "Damage Classes 12 (Knife: base 6 + STR 6); the limit is 5"
    assert found[pump] == "Damage Classes 6; the limit is 5"
    assert found[None] == "Damage Classes 6; the limit is 5"


def test_a_limited_str_power_adds_nothing_to_str(provider):
    doc = _with(_empty(provider), provider,
                _power("STR", 20, Pick("LIMITEDPOWER", 0, None), name="Lift Only"))
    assert None not in _problems(doc, provider, DC(2, ()))
