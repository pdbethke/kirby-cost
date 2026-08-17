"""A power inside a Variable Power Pool costs the character nothing extra.

The pool already buys the capacity, so Java prices its slots at zero toward the
character total — `VariablePowerPool.getRealCostForChild()` is literally
`return 0;`, against Multipower's slot arithmetic and List's pass-through.

The engine was summing the slots into `total_points`, which overcharged every
pool-bearing character by the whole contents of its pool. MENTON-CV1 carries 13
psionic powers in a 250-point pool: 1313 points of slots, and its ledger delta
was exactly 1313.

**The subtlety that decides where the fix goes.** A slot's own `real_cost` is
NOT zero in the oracle's per-object dump — MENTON's Ego Attack is recorded at
150, and the engine already agrees. Only the character total excludes it:

    unparented powers 841 + other sections 683 = 1524 = oracle total_points

and the 13 parented slots (1313) appear nowhere in it. So zeroing
`real_cost_for_child` would be wrong twice over — `real_cost` on a child
delegates to it (`engine/cost.py:175`), so every slot's reported cost would
collapse to 0 and 13 per-object comparisons would break to fix one total.

The totals loop is what must skip them, and only for a VPP: a Multipower's
slots do cost, through `Multipower.real_cost_for_child`.
"""
from tests.corpus import corpus_root
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

_ROOT = (corpus_root() or Path("/nonexistent"))
MENTON = _ROOT / "villains/CV1HDFiles/CV1 HD Files ƒ/MENTON-CV1.hdc"
GRAVITAR = _ROOT / "villains/CV1HDFiles/CV1 HD Files ƒ/GRAVITAR-CV1.hdc"

pytestmark = pytest.mark.skipif(
    not MENTON.exists(), reason="machine-bound HDC corpus absent"
)


@pytest.fixture(scope="module")
def menton():
    return HDCLoader().load_file(str(MENTON))


def _pool(hero):
    for p in hero.powers:
        if type(p).__name__ == "VariablePowerPool":
            return p
    pytest.fail("no VariablePowerPool loaded")


def test_the_pool_slots_are_excluded_from_the_character_total(menton):
    assert menton.total_points == 1524.0


def test_a_slot_still_reports_its_own_cost(menton):
    """The oracle dumps 150 for Mental Assualt — only the TOTAL omits it."""
    slot = next(p for p in menton.powers if p.name == "Mental Assualt")
    assert slot.real_cost == 150.0


def test_the_pool_itself_still_costs(menton):
    """Excluding slots must not exclude the pool that pays for them."""
    assert _pool(menton).real_cost == 430.0


def test_the_slots_are_worth_something_to_exclude(menton):
    """Guards the test above from passing vacuously if parenting breaks."""
    pool = _pool(menton)
    slots = [p for p in menton.powers if getattr(p, "parent", None) is pool]
    assert len(slots) == 13
    assert sum(s.real_cost for s in slots) == 1313.0


@pytest.mark.skipif(not GRAVITAR.exists(), reason="machine-bound HDC corpus absent")
def test_multipower_slots_are_not_affected():
    """A Multipower's slots DO cost — this exclusion is VPP-only."""
    hero = HDCLoader().load_file(str(GRAVITAR))
    mp = next((p for p in hero.powers if type(p).__name__ == "Multipower"), None)
    assert mp is not None
    slots = [p for p in hero.powers if getattr(p, "parent", None) is mp]
    assert slots, "Gravitar's multipower should have slots"
    assert sum(s.real_cost for s in slots) > 0
