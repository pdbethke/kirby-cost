"""A framework knows its own slots, not just the slots their parent.

`List.objects` is Java's `getObjects()` and several rules read it. The loader
linked children upward (`child.parent = framework`) but never populated the
framework's own list, so every framework in the corpus reported zero slots and
any rule that asks the container about its contents silently saw an empty pool.

`Charges.parentUsesEND()` is the rule that exposes it. A Multipower reserve does
not itself use END — its slots do — so Java asks them
(`Charges.java:450-470`)::

    if (parent instanceof com.hero.objects.List) {
        for (GenericObject o : list.getObjects())
            if (childUsesEND(o)) return true;
        return false;
    }

With no objects to iterate the engine concluded the reserve uses no END, which
sets `max = 0` and clamps CHARGES to nothing. DESTROYER_SOLDIER-CV1's D-11
Blaster Rifle is a 30-point reserve whose CHARGES carries a +0.25 advantage:
the oracle prices it 30 x 1.25 = 37.5, round-half-down to 37, and the engine
returned the bare 30. That 7 was the character's whole ledger delta.
"""
from tests.corpus import corpus_root
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects.list import List as HeroList

_ROOT = (corpus_root() or Path("/nonexistent"))
DSOLDIER = (_ROOT / "villains/CV1HDFiles/CV1 HD Files ƒ/DOCTOR_DESTROYER"
            / "DESTROYER_SOLDIER-CV1.hdc")

pytestmark = pytest.mark.skipif(
    not DSOLDIER.exists(), reason="machine-bound HDC corpus absent"
)


@pytest.fixture(scope="module")
def hero():
    return HDCLoader().load_file(str(DSOLDIER))


def _rifle(hero):
    for p in hero.powers:
        if type(p).__name__ == "Multipower":
            return p
    pytest.fail("no Multipower loaded")


def test_the_framework_holds_the_slots_that_point_at_it(hero):
    rifle = _rifle(hero)
    linked = [p for p in hero.powers if getattr(p, "parent", None) is rifle]

    assert linked, "slots must link upward for this test to mean anything"
    assert isinstance(rifle, HeroList)
    assert len(rifle.objects) == len(linked)
    assert {id(o) for o in rifle.objects} == {id(o) for o in linked}


def test_a_reserve_uses_end_when_its_slots_do(hero):
    rifle = _rifle(hero)
    charges = next(m for m in rifle.assigned_modifiers if m.xmlid == "CHARGES")

    assert any(o.uses_end for o in rifle.objects)
    assert charges._parent_uses_end() is True


def test_the_charges_advantage_is_no_longer_clamped_away(hero):
    charges = next(m for m in _rifle(hero).assigned_modifiers if m.xmlid == "CHARGES")
    assert charges.total_value == 0.25


def test_the_reserve_costs_what_the_oracle_says(hero):
    """30 x 1.25 = 37.5 -> 37."""
    assert _rifle(hero).real_cost == 37


def test_the_character_total_matches_the_oracle(hero):
    assert hero.total_points == 227.0
