"""Which slots of one framework can be on together (6E1 401, 404-405, 410,
411, 413). Workshop plan 1b, R15."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from kirby_cost.engine.allocation import fits, pool_of, shares
from kirby_cost.io.formats import load_build
from kirby_cost.objects.frameworks.vpp import VariablePowerPool
from tests.corpus import require_authored_hdc


def _load(name):
    return load_build(str(require_authored_hdc(name)), format="hdc")


def _slot(hero, name):
    (obj,) = [p for p in hero.powers if (p.name or "").strip() == name]
    return obj


@pytest.fixture(scope="module")
def powerlad():
    return _load("PowerLad")


@pytest.fixture(scope="module")
def ravel():
    return _load("Ravel")


def test_a_multipowers_reserve_is_its_base_cost(powerlad):
    """6E1 404: the reserve is the points paid for it before Advantages."""
    assert pool_of(_slot(powerlad, "Rending and Tearing")) == 45


def test_a_power_in_no_framework_shares_nothing(ravel):
    floating = _slot(ravel, "Floating String Form")
    assert pool_of(floating) is None
    assert shares(floating, hero=ravel) == []


def test_a_fixed_slot_always_takes_its_full_active_points(powerlad):
    """6E1 404: a Fixed slot is allocated its Active Points, even when used
    at less."""
    (share,) = shares(_slot(powerlad, "Rending and Tearing"), hero=powerlad)
    assert share.points == 45 and share.power is _slot(powerlad, "Rending and Tearing")


def test_two_fixed_slots_that_overfill_the_reserve_are_never_on_together(powerlad):
    (hka,) = shares(_slot(powerlad, "Rending and Tearing"), hero=powerlad)
    (leap,) = shares(_slot(powerlad, "Iron Grasshopper"), hero=powerlad)
    assert leap.points == 44, "44.5 Active Points: .5 rounds in his favour (6E1 14)"
    assert fits([hka]) and fits([leap])
    assert not fits([hka, leap])


def test_a_variable_slot_may_take_any_share_up_to_its_active_points(ravel):
    """6E1 405: a Variable slot can be given fewer points than its Active
    Points, and then holds what those points buy. ARMaments is an HA 9d6."""
    arm = _slot(ravel, '"ARMaments"')
    got = shares(arm, hero=ravel)
    assert [s.points for s in got] == sorted({s.points for s in got})
    assert got[-1].points == 45 and got[-1].power.levels == 9
    assert got[0].points > 0, "a share of nothing is the slot off, not a share"
    assert any(s.points == 25 and s.power.levels == 5 for s in got)
    assert arm.levels == 9, "each share is a copy; the slot stays as bought"


def test_a_variable_slot_beside_a_fixed_one_fits_in_what_is_left(ravel):
    """6E1 405: a 45-point Fixed slot leaves a 45 reserve nothing to share."""
    arm = shares(_slot(ravel, '"ARMaments"'), hero=ravel)
    (slide,) = shares(_slot(ravel, "String Slide"), hero=ravel)
    assert not any(fits([slide, a]) for a in arm)


def test_slots_of_different_frameworks_never_compete(powerlad, ravel):
    """6E1 401: slots of two frameworks can be used together; each
    framework's own points are what bind."""
    (hka,) = shares(_slot(powerlad, "Rending and Tearing"), hero=powerlad)
    (slide,) = shares(_slot(ravel, "String Slide"), hero=ravel)
    assert fits([hka, slide])


def test_a_vpp_holds_its_pool_in_real_points():
    """6E1 411, 413: the powers in a VPP at once may total no more Real
    Points than the Pool; each is in it as built."""
    vpp = VariablePowerPool()
    vpp.levels = 30
    a = SimpleNamespace(parent=vpp, real_cost_pre_list=15.0, ultra=False, name="a")
    b = SimpleNamespace(parent=vpp, real_cost_pre_list=20.0, ultra=False, name="b")
    assert pool_of(a) == 30
    (sa,), (sb,) = shares(a, hero=None), shares(b, hero=None)
    assert (sa.points, sb.points) == (15, 20)
    assert fits([sa]) and not fits([sa, sb])


def test_a_slot_is_allocated_once(ravel):
    """6E1 410: one allocation a Phase. A slot named twice at one share is
    one slot; at two shares it is two allocations."""
    arm = shares(_slot(ravel, '"ARMaments"'), hero=ravel)
    assert fits([arm[-1], arm[-1]])
    assert arm[0].points + arm[1].points <= 45, "the reserve alone would allow it"
    assert not fits([arm[0], arm[1]])
