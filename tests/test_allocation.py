"""Pricing a power at a smaller Multipower allocation (6E1 p.405-406)."""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.engine.allocation import LevelFit, NotLadderable, ladder, levels_within
from kirby_cost.services.power_builder import build_power_from_spec

RE_FLIGHT = {"xmlid": "FLIGHT", "levels": 50,
             "modifiers": [{"xmlid": "REDUCEDEND", "option_id": "HALFEND"}]}


def test_drain_6d6_at_40_points_is_4d6():            # p.405
    p, _, _ = build_power_from_spec({"xmlid": "DRAIN", "levels": 6, "modifiers": []})
    assert levels_within(p, 40).levels == 4


def test_blast_12d6_at_20_points_is_4d6():           # p.406 Kerendor
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    fit = levels_within(p, 20)
    assert (fit.levels, fit.active_points, fit.display) == (4, 20, "4d6")


def test_flight_50m_reduced_end_at_30_points_is_24m():  # p.406: the +1/4 is paid out of the allocation
    p, _, _ = build_power_from_spec(RE_FLIGHT)
    fit = levels_within(p, 30)
    assert (fit.levels, fit.active_points) == (24, 30)
    assert fit.display == "24m"


def test_zero_points_is_nothing():
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    fit = levels_within(p, 0)
    assert (fit.levels, fit.active_points) == (0, 0)


def test_full_points_is_the_power_as_bought():
    p, active, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    assert levels_within(p, active).levels == 12


def test_the_fit_is_an_independent_copy():
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    fit = levels_within(p, 20)
    assert fit.power is not p and fit.power.levels == 4 and p.levels == 12


def test_ladder_steps_are_ascending_and_end_at_full():
    p, active, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    steps = ladder(p)
    assert all(isinstance(s, LevelFit) for s in steps)
    aps = [s.active_points for s in steps]
    assert aps == sorted(set(aps))
    assert steps[0].levels == 0 and steps[-1].active_points == active


def test_ladder_leaves_the_original_untouched():
    p, active, _ = build_power_from_spec(RE_FLIGHT)
    parents = [m.parent for m in p.assigned_modifiers]
    ladder(p)
    levels_within(p, 30)
    assert p.levels == 50 and p.active_cost == active
    assert [m.parent for m in p.assigned_modifiers] == parents
    assert all(m.parent is p for m in p.assigned_modifiers)


def test_a_power_not_driven_by_levels_is_not_ladderable():
    p, _, _ = build_power_from_spec({"xmlid": "DRAIN", "levels": 0, "modifiers": []})
    with pytest.raises(NotLadderable):
        levels_within(p, 10)


def _half_die_blast(adder_xmlid):
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 8, "modifiers": []})
    from kirby_cost.objects.adder import Adder
    ad = Adder()
    ad.xmlid = adder_xmlid
    ad._selected = True
    loader = HDCLoader()
    loader._ensure_registry_loaded()
    loader._apply_template_to_adder(ad, "ENERGYBLAST", adder_xmlid)
    p._assigned_adders.append(ad)
    return p


def test_half_die_slot_has_half_die_steps():
    p = _half_die_blast("PLUSONEHALFDIE")
    full = p.active_cost
    steps = ladder(p)
    halves = [s for s in steps if s.half_die]
    assert halves and all(s.display.endswith("1/2d6") for s in halves)
    assert steps[-1].half_die and steps[-1].active_points == full
    # a step under the full cost can be a whole-die step, so both kinds appear
    assert any(not s.half_die and s.levels > 0 for s in steps)


def test_slot_without_half_die_never_gains_one():
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 8, "modifiers": []})
    assert not any(s.half_die for s in ladder(p))
