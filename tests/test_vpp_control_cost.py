"""A VPP's control cost comes from its CONTROLCOST adder, which the file supplies.

`VariablePowerPool.__init__` synthesises a required CONTROLCOST adder, mirroring
Java's `init()`, at `LVLCOST=1 / LVLVAL=2` with no levels. The character file
supplies the levels:

    <VPP XMLID="GENERIC_OBJECT" NAME="Minor String Tricks" LEVELS="20" BASECOST="0.0">
      <ADDER XMLID="CONTROLCOST" LEVELS="10" LVLCOST="1.0" LVLVAL="2.0"
             REQUIRED="Yes"/>

but the loader's framework branch read only `<MODIFIER>` children, never
`<ADDER>` ones, so the synthesised stub survived at 0 levels and every pool in
the corpus costed its control at 0.

Java, `VariablePowerPool.getTotalCost()` (6E branch) and `getActiveCost()`:

    total  = roundHalfDown(levels / levelValue * levelCost)   # the pool
           + CONTROLCOST adder total, if present
           + every NON-required assigned/private adder total

    active = (total - pool) * (1 + advantages) + pool

For Ravel's pool (a Gadget Pool of 20): CONTROLCOST 10/2*1 = 5, so total 25. Its
one PRIVATE modifier (HALFPHASE +1/2) gives advantages 0.5, so
active = (25 - 20) * 1.5 + 20 = 27.5, which HD rounds half down to 27 — against
the engine's 20 before the adder was read.

Advantages apply to the control cost and other adders but never to the pool
itself, which is why the pool is subtracted out and added back.
"""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.corpus import require_authored_hdc


@pytest.fixture(scope="module")
def pool():
    hero = HDCLoader().load_file(str(require_authored_hdc("Ravel")))
    for p in hero.powers:
        if type(p).__name__ == "VariablePowerPool":
            return p
    pytest.fail("no VariablePowerPool loaded")


def test_the_control_cost_adder_keeps_the_levels_the_file_gave_it(pool):
    control = [a for a in pool.assigned_adders if a.xmlid == "CONTROLCOST"]
    assert len(control) == 1, "the file's adder must update the stub, not duplicate it"
    assert control[0].levels == 10


def test_control_cost_is_a_quarter_of_the_pool_here(pool):
    """LEVELS=10 at LVLCOST 1 per LVLVAL 2 -> 5."""
    assert pool.pool_cost == 20.0
    assert pool.control_cost == 5.0


def test_total_cost_is_pool_plus_control(pool):
    assert pool.total_cost == 25.0


def test_advantages_apply_to_the_control_cost_but_not_the_pool(pool):
    """(25 - 20) * (1 + 0.5) + 20 = 27.5 -> 27; the pool's Limitations then
    bring the real cost to 24."""
    assert pool.active_cost == 27
    assert pool.real_cost == 24


def test_the_character_total_matches_the_oracle():
    """The control cost is part of the character's spent points."""
    hero = HDCLoader().load_file(str(require_authored_hdc("Ravel")))
    assert hero.total_points == 450.0
