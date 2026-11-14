"""A power inside a Variable Power Pool costs the character nothing extra.

The pool already buys the capacity, so Java prices its slots at zero toward the
character total — `VariablePowerPool.getRealCostForChild()` is literally
`return 0;`, against Multipower's slot arithmetic and List's pass-through.

The engine was summing the slots into `total_points`, which overcharged every
pool-bearing character by the whole contents of its pool. A corpus character with
13 psionic powers in a 250-point pool carried 1313 points of slots, and its
ledger delta was exactly 1313. The tests below add a slot to Ravel's own pool.

**What the oracle's 150 actually is.** This file used to argue that
`real_cost_for_child` must NOT return zero, because the oracle's per-object
dump records 150 for a slot. That reading was wrong: the dumper emits
`getRealCostPreList()` for that field (CostCalculatorCLI.java:394), not
`getRealCost()`. Pre-list is the slot's own price whether or not the parent zeroes it, so the
dump never contradicted `return 0` — and `return 0` is what Java does.

The distinction is visible on the sheet. HD prints "(N Active Points)" on a
pooled Entangle, which getModifierString only does when
`getRealCost() != getTotalCost()`; with a non-zero slot cost all three
numbers agree and the note disappears.

So a slot's real cost is 0 and its PRE-LIST cost is its own price. The
character total is the same with or without the slots, because the parented
slots appear nowhere in it. The totals
loop skips them explicitly as well, which is now belt-and-braces rather than
the mechanism. This is VPP-only: a Multipower's slots do cost, through
`Multipower.real_cost_for_child`.
"""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.corpus import require_authored_hdc
from tests.own_copy import own_copy

SLOT_NAME = "Probe Blast"


def _slot_xml(pool_id):
    """A 10d6 Energy Blast bought inside the pool: 50 active points, 29 after the
    pool's own Limitations (its Gadget Pool framework)."""
    return (f'<POWER XMLID="ENERGYBLAST" ID="9000000000030" BASECOST="0.0" LEVELS="10" '
            f'ALIAS="Energy Blast" POSITION="99" MULTIPLIER="1.0" PARENTID="{pool_id}" '
            f'NAME="{SLOT_NAME}" QUANTITY="1" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes" '
            f'INPUT="ED" />')


def _pool_id():
    from lxml import etree
    root = etree.parse(str(require_authored_hdc("Ravel"))).getroot()
    return root.find(".//VPP").get("ID")


@pytest.fixture
def ravel():
    return HDCLoader().load_file(str(require_authored_hdc("Ravel")))


@pytest.fixture
def pooled(tmp_path):
    """Ravel with one slot added to his Variable Power Pool."""
    return HDCLoader().load_file(own_copy(
        tmp_path, "Ravel", section_xml=[("POWERS", _slot_xml(_pool_id()))]))


def _pool(hero):
    for p in hero.powers:
        if type(p).__name__ == "VariablePowerPool":
            return p
    pytest.fail("no VariablePowerPool loaded")


def test_the_pool_slots_are_excluded_from_the_character_total(pooled, ravel):
    assert pooled.total_points == ravel.total_points


def test_a_slot_still_reports_its_own_cost(pooled):
    """The oracle dumps a slot's own price -- as its PRE-LIST cost."""
    slot = next(p for p in pooled.powers if p.name == SLOT_NAME)
    assert slot.real_cost_pre_list == 29.0


def test_a_slot_costs_the_character_nothing(pooled):
    """VariablePowerPool.getRealCostForChild is literally `return 0`."""
    slot = next(p for p in pooled.powers if p.name == SLOT_NAME)
    assert slot.real_cost == 0.0


def test_the_pool_itself_still_costs(pooled, ravel):
    """Excluding slots must not exclude the pool that pays for them."""
    assert _pool(pooled).real_cost == _pool(ravel).real_cost == 24.0


def test_the_slots_are_worth_something_to_exclude(pooled):
    """Guards the test above from passing vacuously if parenting breaks."""
    pool = _pool(pooled)
    slots = [p for p in pooled.powers if getattr(p, "parent", None) is pool]
    assert len(slots) == 1
    assert sum(s.real_cost_pre_list for s in slots) == 29.0
    assert sum(s.real_cost for s in slots) == 0.0


def test_multipower_slots_are_not_affected():
    """A Multipower's slots DO cost — this exclusion is VPP-only."""
    hero = HDCLoader().load_file(str(require_authored_hdc("PowerLad")))
    mp = next((p for p in hero.powers if type(p).__name__ == "Multipower"), None)
    assert mp is not None
    slots = [p for p in hero.powers if getattr(p, "parent", None) is mp]
    assert slots, "PowerLad's multipower should have slots"
    assert sum(s.real_cost for s in slots) > 0
