"""A VPP's control cost comes from its CONTROLCOST adder, which the file supplies.

`VariablePowerPool.__init__` synthesises a required CONTROLCOST adder, mirroring
Java's `init()`, at `LVLCOST=1 / LVLVAL=2` with no levels. The character file
supplies the levels:

    <VPP XMLID="GENERIC_OBJECT" NAME="Demonic Powers" LEVELS="40" BASECOST="0.0">
      <ADDER XMLID="CONTROLCOST" LEVELS="40" LVLCOST="1.0" LVLVAL="2.0"
             REQUIRED="Yes"/>

but the loader's framework branch read only `<MODIFIER>` children, never
`<ADDER>` ones, so the synthesised stub survived at 0 levels and every pool in
the corpus costed its control at 0.

Java, `VariablePowerPool.getTotalCost()` (6E branch) and `getActiveCost()`:

    total  = roundHalfDown(levels / levelValue * levelCost)   # the pool
           + CONTROLCOST adder total, if present
           + every NON-required assigned/private adder total

    active = (total - pool) * (1 + advantages) + pool

For GREATER_DEMON_HSB: pool 40, CONTROLCOST 40/2*1 = 20, so total 60. Its two
PRIVATE modifiers (ZEROPHASE +1, NOSKILLROLL +1) give advantages 2.0, so
active = (60 - 40) * 3 + 40 = 100 — the oracle's number, against the engine's 40.

Advantages apply to the control cost and other adders but never to the pool
itself, which is why the pool is subtracted out and added back.
"""
from tests.corpus import corpus_root
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

DEMON = Path(
    str(corpus_root() or "/nonexistent") + "/"
    "bestiary/HERO_System_Bestiary_6th_Edition_Character_Pack/HSB HD Files/"
    "CHAPTER_2/DEMONS_AND_DEVILS/GREATER_DEMON_HSB.hdc"
)

pytestmark = pytest.mark.skipif(
    not DEMON.exists(), reason="machine-bound HDC corpus absent"
)


@pytest.fixture(scope="module")
def pool():
    hero = HDCLoader().load_file(str(DEMON))
    for p in hero.powers:
        if type(p).__name__ == "VariablePowerPool":
            return p
    pytest.fail("no VariablePowerPool loaded")


def test_the_control_cost_adder_keeps_the_levels_the_file_gave_it(pool):
    control = [a for a in pool.assigned_adders if a.xmlid == "CONTROLCOST"]
    assert len(control) == 1, "the file's adder must update the stub, not duplicate it"
    assert control[0].levels == 40


def test_control_cost_is_half_the_pool_here(pool):
    """LEVELS=40 at LVLCOST 1 per LVLVAL 2 -> 20."""
    assert pool.pool_cost == 40.0
    assert pool.control_cost == 20.0


def test_total_cost_is_pool_plus_control(pool):
    assert pool.total_cost == 60.0


def test_advantages_apply_to_the_control_cost_but_not_the_pool(pool):
    """(60 - 40) * (1 + 2.0) + 40 = 100."""
    assert pool.active_cost == 100.0
    assert pool.real_cost == 100.0


def test_the_character_total_matches_the_oracle():
    """The whole -60 ledger delta for this character was this one pool."""
    hero = HDCLoader().load_file(str(DEMON))
    assert hero.total_points == 1078.0
