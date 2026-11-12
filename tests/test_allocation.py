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


def test_equal_cost_steps_keep_the_most_levels():
    # Telekinesis is level_value 2: levels 5 and 6 cost the same 9 points,
    # so the points buy 6, never 5 (cost.py rounds the unit count up).
    p, _, _ = build_power_from_spec({"xmlid": "TELEKINESIS", "levels": 8, "modifiers": []})
    assert levels_within(p, 9).levels == 6
    assert levels_within(p, 11).levels == 6
    assert [s.levels for s in ladder(p)] == [0, 2, 4, 6, 8]


# ── Task 2: multi-level defences and characteristic slots ──────────────────

def _resistant(pd, ed, **extra):
    spec = {"xmlid": "FORCEFIELD", "pd_levels": pd, "ed_levels": ed, "modifiers": []}
    spec.update(extra)
    return build_power_from_spec(spec)


def test_resistant_protection_15_15_at_9_points_is_3_3():   # 6E1 p.406 Kerendor
    p, _, _ = _resistant(15, 15)
    fit = levels_within(p, 9)
    assert (fit.power.pd_levels, fit.power.ed_levels, fit.active_points) == (3, 3, 9)


def test_spec_levels_default_to_the_sum_of_the_defence_fields():
    p, active, _ = _resistant(25, 20)
    assert p.levels == 45 and active == 69        # HD writes LEVELS=45 for 25/20; 23 units of 3


def test_resistant_protection_steps_the_fields_together_floored():
    p, active, _ = _resistant(20, 10)
    fit = levels_within(p, 9)          # 6 levels buy 2/4 of the 30: a third of each
    assert (fit.power.pd_levels, fit.power.ed_levels) == (4, 2)
    assert fit.power.levels == 6 and fit.active_points == 9


def test_resistant_protection_ladder_ends_at_the_power_as_bought():
    p, active, _ = _resistant(15, 15)
    top = ladder(p)[-1]
    assert (top.power.pd_levels, top.power.ed_levels, top.active_points) == (15, 15, active)
    assert ladder(p)[0].power.pd_levels == 0


def test_resistant_protection_ladder_leaves_the_original_untouched():
    p, active, _ = _resistant(15, 15)
    levels_within(p, 9)
    assert (p.pd_levels, p.ed_levels, p.levels, p.active_cost) == (15, 15, 30, active)


def test_resistant_protection_fields_never_exceed_what_was_bought():
    p, _, _ = _resistant(25, 20, md_levels=5)
    for step in ladder(p):
        f = step.power
        assert f.pd_levels <= 25 and f.ed_levels <= 20 and f.md_levels <= 5
        assert f.levels == f.pd_levels + f.ed_levels + f.md_levels + f.powd_levels


@pytest.mark.parametrize("xmlid", ["STR", "DEX", "PD", "ED", "SPD"])
def test_characteristic_slots_ladder_by_points_of_the_characteristic(xmlid):
    p, active, _ = build_power_from_spec({"xmlid": xmlid, "levels": 10, "modifiers": []})
    full = levels_within(p, active)
    assert full.levels == 10 and full.active_points == active
    half = levels_within(p, active // 2)
    assert 0 < half.levels < 10 and half.active_points <= active // 2


def test_str_20_in_a_10_point_share_is_str_10():
    p, _, _ = build_power_from_spec({"xmlid": "STR", "levels": 20, "modifiers": []})
    assert levels_within(p, 10).levels == 10


def test_cloned_adders_are_parented_to_the_copy():
    p = _half_die_blast("PLUSONEHALFDIE")
    for ad in p._assigned_adders:
        ad.parent = p
    fit = levels_within(p, 20)
    assert all(a.parent is fit.power for a in fit.power._assigned_adders)
    assert all(a.parent is p for a in p._assigned_adders)


def test_clone_itself_reparents_adders_before_any_costing():
    # levels_within reads active_cost, which re-parents as a side effect; the
    # clone must be right on its own, before anything is costed.
    from kirby_cost.engine.allocation import _clone
    p = _half_die_blast("PLUSONEHALFDIE")
    for ad in p._assigned_adders:
        ad.parent = p
    dup = _clone(p)
    assert dup._assigned_adders and all(a.parent is dup for a in dup._assigned_adders)
    assert all(a.parent is p for a in p._assigned_adders)
    assert not any(a is b for a in dup._assigned_adders for b in p._assigned_adders)


def test_forcefield_spec_with_no_levels_and_no_split_raises():
    with pytest.raises(ValueError, match="pd_levels"):
        build_power_from_spec({"xmlid": "FORCEFIELD", "modifiers": []})


def test_forcefield_spec_with_one_split_field_leaves_the_rest_unbought():
    p, _, _ = build_power_from_spec({"xmlid": "FORCEFIELD", "pd_levels": 10, "modifiers": []})
    assert (p.levels, p.pd_levels, p.ed_levels) == (10, 10, 0)


def test_resistant_protection_top_step_is_the_power_as_bought_even_if_levels_differ():
    p, active, _ = _resistant(15, 15, levels=31)
    top = ladder(p)[-1]
    assert (top.levels, top.active_points) == (31, active)


def test_hkb_style_zero_level_half_die_slot_ladders_as_nothing_and_full():
    p, active, _ = build_power_from_spec({"xmlid": "HKA", "levels": 0, "modifiers": []})
    from kirby_cost.objects.adder import Adder
    ad = Adder(); ad.xmlid = "PLUSONEHALFDIE"; ad._selected = True
    loader = HDCLoader(); loader._ensure_registry_loaded()
    loader._apply_template_to_adder(ad, "HKA", "PLUSONEHALFDIE")
    p._assigned_adders.append(ad)
    full = int(round(p.active_cost))
    assert full > 0
    steps = ladder(p)
    assert [(s.levels, s.active_points) for s in steps] == [(0, 0), (0, full)]
    assert steps[-1].half_die and steps[-1].display.startswith("1/2d6")
    assert levels_within(p, full - 1).active_points == 0
    assert levels_within(p, full).active_points == full
