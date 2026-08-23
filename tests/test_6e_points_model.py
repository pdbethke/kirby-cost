"""The HERO System 6th Edition character-points model.

HD's own ``LoadedHero.available_points`` (``hdc_loader.py``) is 5th-Edition
arithmetic: Complications ADD to the pool. 6E changed this —

- 6E1 p.30: falling short of the campaign's Matching Complications target
  reduces Total Points 1:1; taking MORE than the target buys nothing extra.
- 6E1 p.269: the campaign's Total Points figure (HDC ``BASE_POINTS``)
  ALREADY INCLUDES the matching complications.

``complications_shortfall`` / ``spendable_points`` / ``points_unspent``
implement that printed rule, alongside (never replacing) HD's own
``available_points``. This file proves both readings, on the same
characters, disagree exactly the way the two rulebooks disagree.

Worked examples are the three authored characters (Ravel, Bokor, Power Lad —
see ``tests/fixtures/authored/``) plus the bestiary's Elemental - Air, which
took NO complications against a 50-point target. The authored .hdc files are
machine-bound (``KIRBY_COST_AUTHORED``, see ``tests/test_authored_characters.py``)
so those three are hand-built here from the committed oracle JSON dumps
instead of loaded live; Elemental - Air's .hdc ships in this repo's own
oracle corpus and is loaded for real.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader, LoadedHero
from tests.conftest import make_object

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "authored"
ELEMENTAL_AIR_FIXTURE = (
    Path(__file__).parent / "fixtures" / "oracle"
    / "bestiary__HERO_System_Bestiary_6th_Edition_Character_Pack__HSB HD Files"
      "__CHAPTER_1__CREATURE_TEMPLATES__ELEMENTAL_AIR-HSB.json"
)


def _hand_built(*, base_points, disad_points, experience, taken, spent) -> LoadedHero:
    """A LoadedHero with just enough state to exercise the points model.

    ``total_points`` is a computed property (it walks characteristics/
    skills/perks/talents/martial_arts/powers and sums real_cost), so a single
    synthetic power whose base_cost equals *spent* reproduces it exactly.
    ``disads_used`` likewise sums real_cost over ``complications``, so one
    synthetic complication whose base_cost equals *taken* reproduces it.
    """
    hero = LoadedHero()
    hero.base_points = base_points
    hero.disad_points = disad_points
    hero.experience = experience
    if spent:
        hero.powers.append(make_object(base_cost=spent, xmlid="TEST_SPENT"))
    if taken:
        hero.complications.append(make_object(base_cost=taken, xmlid="TEST_TAKEN"))
    return hero


# name -> (base_points, disad_points, experience, taken, spent, hd_left, sixe_left)
WORKED_EXAMPLES = {
    "Ravel": (400, 100, 50, 100, 450.0, 100.0, 0.0),
    "PowerLad": (400, 120, 0, 120, 399.5, 120.5, 0.5),
    "Bokor": (270, 40, 5, 40, 276.0, 39.0, -1.0),
}


@pytest.mark.parametrize("name", sorted(WORKED_EXAMPLES))
def test_worked_examples_hand_built(name):
    base, disad, exp, taken, spent, hd_left, sixe_left = WORKED_EXAMPLES[name]
    hero = _hand_built(
        base_points=base, disad_points=disad, experience=exp,
        taken=taken, spent=spent,
    )
    assert hero.total_points == spent
    assert hero.available_points == hd_left
    assert hero.points_unspent == sixe_left


@pytest.mark.parametrize("name", sorted(WORKED_EXAMPLES))
def test_worked_examples_match_committed_oracle_fixture(name):
    """The hand-built heroes above are not invented numbers — they are the
    committed oracle JSON dumps for these three characters, restated."""
    fixture = FIXTURE_DIR / f"{name}.json"
    if not fixture.exists():
        pytest.skip(f"{fixture} not present")
    oracle = json.loads(fixture.read_text())
    base, disad, exp, taken, spent, hd_left, sixe_left = WORKED_EXAMPLES[name]
    assert oracle["total_points"] == spent
    assert oracle["available_points"] == hd_left
    comps = oracle.get("complications") or []
    assert sum(c.get("real_cost", 0) for c in comps) == taken


def test_elemental_air_took_no_complications_and_loses_the_whole_target():
    """Real corpus character, loaded live. Took 0 of a 50-point Matching
    Complications target: the whole 50 comes off spendable_points, on top
    of whatever total_points already spent — 6E1 p.30's "every 1 point
    short reduces Total Points by 1" taken to its floor."""
    if not ELEMENTAL_AIR_FIXTURE.exists():
        pytest.skip("oracle fixture not present")
    oracle = json.loads(ELEMENTAL_AIR_FIXTURE.read_text())
    hdc_path = oracle["hdc_path"]
    if not Path(hdc_path).exists():
        pytest.skip(f"HDC file missing: {hdc_path}")

    hero = HDCLoader().load_file(hdc_path)

    assert hero.total_points == 200.0
    assert hero.available_points == -25.0
    assert hero.disads_used == 0
    assert hero.base_points == 175
    assert hero.disad_points == 50
    assert hero.complications_shortfall == 50.0
    assert hero.spendable_points == 125.0  # 175 base - 50 shortfall, no exp
    assert hero.points_unspent == -75.0


def test_shortfall_costs_one_for_one_below_the_target():
    hero = _hand_built(base_points=200, disad_points=50, experience=0,
                        taken=20, spent=100)
    assert hero.complications_shortfall == 30.0
    assert hero.spendable_points == 200 - 30.0
    assert hero.points_unspent == (200 - 30.0) - 100


def test_excess_complications_grant_nothing():
    """Taking MORE than the target must not raise spendable_points above the
    at-target figure — 6E1 p.30's parenthetical, the half of the rule most
    likely to be implemented as if surplus complications paid out."""
    at_target = _hand_built(base_points=200, disad_points=50, experience=0,
                             taken=50, spent=100)
    over_target = _hand_built(base_points=200, disad_points=50, experience=0,
                               taken=90, spent=100)
    assert at_target.complications_shortfall == 0.0
    assert over_target.complications_shortfall == 0.0
    assert over_target.spendable_points == at_target.spendable_points
    assert over_target.spendable_points == 200.0


def test_points_unspent_is_negative_when_overspent():
    """Bokor: built to 276 against a 6E pool of 275 (270 - 0 shortfall + 5
    exp) — one point over. Must not be clamped to zero."""
    hero = _hand_built(base_points=270, disad_points=40, experience=5,
                        taken=40, spent=276.0)
    assert hero.spendable_points == 275.0
    assert hero.points_unspent == -1.0
    assert hero.points_unspent < 0


def test_available_points_parity_guard_untouched():
    """available_points must still be exactly HD's formula, unaffected by
    the 6E properties added alongside it."""
    hero = _hand_built(base_points=270, disad_points=40, experience=5,
                        taken=40, spent=276.0)
    assert hero.available_points == (
        hero.base_points + hero.disads_used + hero.experience - hero.total_points
    )
    assert hero.available_points == 39.0


def test_powerlad_fraction_survives_uncoerced():
    """Power Lad's 0.5 must not be narrowed to an int anywhere in the new
    properties (spendable_points, points_unspent)."""
    base, disad, exp, taken, spent, hd_left, sixe_left = WORKED_EXAMPLES["PowerLad"]
    hero = _hand_built(base_points=base, disad_points=disad, experience=exp,
                        taken=taken, spent=spent)
    assert hero.total_points == 399.5
    assert hero.points_unspent == 0.5
    assert hero.points_unspent * 2 == 1.0  # would silently become 0 if narrowed to int
