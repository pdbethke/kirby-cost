"""Pricing a power at a smaller Multipower allocation (6E1 p.405-406)."""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.engine.allocation import (
    LevelFit, NotLadderable, ladder, levels_within, slot_words, step_display,
)
from kirby_cost.services.power_builder import build_power_from_spec

RE_FLIGHT = {"xmlid": "FLIGHT", "levels": 50,
             "modifiers": [{"xmlid": "REDUCEDEND", "option_id": "HALFEND"}]}


def test_drain_6d6_at_40_points_is_4d6():            # p.405
    p, _, _ = build_power_from_spec({"xmlid": "DRAIN", "levels": 6, "modifiers": []})
    assert levels_within(p, 40, hero=None).levels == 4


def test_blast_12d6_at_20_points_is_4d6():           # p.406 Kerendor
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    fit = levels_within(p, 20, hero=None)
    assert (fit.levels, fit.active_points, fit.display) == (4, 20, "4d6")


def test_flight_50m_reduced_end_at_30_points_is_24m():  # p.406: the +1/4 is paid out of the allocation
    p, _, _ = build_power_from_spec(RE_FLIGHT)
    fit = levels_within(p, 30, hero=None)
    assert (fit.levels, fit.active_points) == (24, 30)
    assert fit.display == "24m"


def test_zero_points_is_nothing():
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    fit = levels_within(p, 0, hero=None)
    assert (fit.levels, fit.active_points) == (0, 0)


def test_full_points_is_the_power_as_bought():
    p, active, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    assert levels_within(p, active, hero=None).levels == 12


def test_the_fit_is_an_independent_copy():
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    fit = levels_within(p, 20, hero=None)
    assert fit.power is not p and fit.power.levels == 4 and p.levels == 12


def test_ladder_steps_are_ascending_and_end_at_full():
    p, active, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    steps = ladder(p, hero=None)
    assert all(isinstance(s, LevelFit) for s in steps)
    aps = [s.active_points for s in steps]
    assert aps == sorted(set(aps))
    assert steps[0].levels == 0 and steps[-1].active_points == active


def test_ladder_leaves_the_original_untouched():
    p, active, _ = build_power_from_spec(RE_FLIGHT)
    parents = [m.parent for m in p.assigned_modifiers]
    ladder(p, hero=None)
    levels_within(p, 30, hero=None)
    assert p.levels == 50 and p.active_cost == active
    assert [m.parent for m in p.assigned_modifiers] == parents
    assert all(m.parent is p for m in p.assigned_modifiers)


def test_a_power_not_driven_by_levels_is_not_ladderable():
    p, _, _ = build_power_from_spec({"xmlid": "DRAIN", "levels": 0, "modifiers": []})
    with pytest.raises(NotLadderable):
        levels_within(p, 10, hero=None)


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
    steps = ladder(p, hero=None)
    halves = [s for s in steps if s.half_die]
    assert halves and all(s.display.endswith("1/2d6") for s in halves)
    assert steps[-1].half_die and steps[-1].active_points == full
    # a step under the full cost can be a whole-die step, so both kinds appear
    assert any(not s.half_die and s.levels > 0 for s in steps)


def test_slot_without_half_die_never_gains_one():
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 8, "modifiers": []})
    assert not any(s.half_die for s in ladder(p, hero=None))


def test_equal_cost_steps_keep_the_most_levels():
    # Telekinesis is level_value 2: levels 5 and 6 cost the same 9 points,
    # so the points buy 6, never 5 (cost.py rounds the unit count up).
    p, _, _ = build_power_from_spec({"xmlid": "TELEKINESIS", "levels": 8, "modifiers": []})
    assert levels_within(p, 9, hero=None).levels == 6
    assert levels_within(p, 11, hero=None).levels == 6
    assert [s.levels for s in ladder(p, hero=None)] == [0, 2, 4, 6, 8]


# ── Task 2: multi-level defences and characteristic slots ──────────────────

def _resistant(pd, ed, **extra):
    spec = {"xmlid": "FORCEFIELD", "pd_levels": pd, "ed_levels": ed, "modifiers": []}
    spec.update(extra)
    return build_power_from_spec(spec)


def test_resistant_protection_15_15_at_9_points_is_3_3():   # 6E1 p.406 Kerendor
    p, _, _ = _resistant(15, 15)
    fit = levels_within(p, 9, hero=None)
    assert (fit.power.pd_levels, fit.power.ed_levels, fit.active_points) == (3, 3, 9)


def test_spec_levels_default_to_the_sum_of_the_defence_fields():
    p, active, _ = _resistant(25, 20)
    assert p.levels == 45 and active == 69        # HD writes LEVELS=45 for 25/20; 23 units of 3


def test_resistant_protection_steps_the_fields_together_floored():
    p, active, _ = _resistant(20, 10)
    fit = levels_within(p, 9, hero=None)          # 6 levels buy 2/4 of the 30: a third of each
    assert (fit.power.pd_levels, fit.power.ed_levels) == (4, 2)
    assert fit.power.levels == 6 and fit.active_points == 9


def test_resistant_protection_ladder_ends_at_the_power_as_bought():
    p, active, _ = _resistant(15, 15)
    top = ladder(p, hero=None)[-1]
    assert (top.power.pd_levels, top.power.ed_levels, top.active_points) == (15, 15, active)
    assert ladder(p, hero=None)[0].power.pd_levels == 0


def test_resistant_protection_ladder_leaves_the_original_untouched():
    p, active, _ = _resistant(15, 15)
    levels_within(p, 9, hero=None)
    assert (p.pd_levels, p.ed_levels, p.levels, p.active_cost) == (15, 15, 30, active)


def test_resistant_protection_fields_never_exceed_what_was_bought():
    p, _, _ = _resistant(25, 20, md_levels=5)
    for step in ladder(p, hero=None):
        f = step.power
        assert f.pd_levels <= 25 and f.ed_levels <= 20 and f.md_levels <= 5
        assert f.levels == f.pd_levels + f.ed_levels + f.md_levels + f.powd_levels


@pytest.mark.parametrize("xmlid", ["STR", "DEX", "PD", "ED", "SPD"])
def test_characteristic_slots_ladder_by_points_of_the_characteristic(xmlid):
    p, active, _ = build_power_from_spec({"xmlid": xmlid, "levels": 10, "modifiers": []})
    full = levels_within(p, active, hero=None)
    assert full.levels == 10 and full.active_points == active
    half = levels_within(p, active // 2, hero=None)
    assert 0 < half.levels < 10 and half.active_points <= active // 2


def test_str_20_in_a_10_point_share_is_str_10():
    p, _, _ = build_power_from_spec({"xmlid": "STR", "levels": 20, "modifiers": []})
    assert levels_within(p, 10, hero=None).levels == 10


def test_cloned_adders_are_parented_to_the_copy():
    p = _half_die_blast("PLUSONEHALFDIE")
    for ad in p._assigned_adders:
        ad.parent = p
    fit = levels_within(p, 20, hero=None)
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
    top = ladder(p, hero=None)[-1]
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
    steps = ladder(p, hero=None)
    assert [(s.levels, s.active_points) for s in steps] == [(0, 0), (0, full)]
    assert steps[-1].half_die and steps[-1].display == "1/2d6"
    assert levels_within(p, full - 1, hero=None).active_points == 0
    assert levels_within(p, full, hero=None).active_points == full


# ── what a rung reads as (6E1 p.406, Kerendor) ─────────────────────────────
# The menu that offers a split says what each share buys in HD's own words:
# the power's name and its damage display, and for Resistant Protection the
# PD/ED it was bought as, which HD prints in column 2 rather than as a
# damage display.

def test_step_display_names_the_power_and_its_dice():
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []})
    assert step_display(levels_within(p, 30, hero=None).power, hero=None) == "Blast 6d6"


def test_step_display_names_flight_and_its_metres():
    p, _, _ = build_power_from_spec({"xmlid": "FLIGHT", "levels": 60, "modifiers": []})
    assert step_display(levels_within(p, 30, hero=None).power, hero=None) == "Flight 30m"


def test_step_display_of_resistant_protection_states_pd_and_ed():
    p, _, _ = build_power_from_spec(
        {"xmlid": "FORCEFIELD", "pd_levels": 15, "ed_levels": 15, "modifiers": []})
    assert step_display(p, hero=None) == "Resistant Protection 15 PD/15 ED"
    assert step_display(levels_within(p, 9, hero=None).power, hero=None) == "Resistant Protection 3 PD/3 ED"


def test_resistant_protection_column2_keeps_hd_wording():
    """The PD/ED list moved into `ForceField.defence_levels_display`; column 2
    still prints it inside HD's parentheses."""
    p, _, _ = build_power_from_spec(
        {"xmlid": "FORCEFIELD", "pd_levels": 15, "ed_levels": 15, "modifiers": []})
    assert "(15 PD/15 ED)" in p.column2_output


def test_step_display_of_power_defense_names_each_rungs_amount():
    p, _, _ = build_power_from_spec({"xmlid": "POWERDEFENSE", "levels": 20, "modifiers": []})
    assert step_display(levels_within(p, 5, hero=None).power, hero=None) == "Power Defense 5 points"
    assert step_display(levels_within(p, 10, hero=None).power, hero=None) == "Power Defense 10 points"


def test_step_display_of_a_characteristic_bought_in_a_slot_names_its_amount():
    """PD bought as a Multipower slot has no damage display; HD writes the
    amount in column 2 ("+20 PD"), and a rung says the same."""
    p, _, _ = build_power_from_spec({"xmlid": "PD", "levels": 20, "modifiers": []})
    p.levels = 20
    assert step_display(levels_within(p, 5, hero=None).power, hero=None) == "+5 PD"
    assert step_display(p, hero=None) == "+20 PD"


def test_a_power_with_no_defence_split_says_nothing_of_one():
    p, _, _ = build_power_from_spec({"xmlid": "ENERGYBLAST", "levels": 4, "modifiers": []})
    assert p.defence_levels_display() == ""


# ── the words do not depend on whichever hero was loaded last (I5) ─────────
# An HKA's display carries HD's "w/STR" bracket, read off kirby-cost's
# process-wide active hero. A long-lived process (a fight holds many heroes)
# must get the same rung text for a slot whichever hero it loaded last, so
# `ladder`, `levels_within` and `step_display` are told whose power it is.

def _loaded(name: str):
    from tests.corpus import require_authored_hdc
    return HDCLoader().load_file(str(require_authored_hdc(name)))


def _hka_slot(hero):
    return next(p for p in hero.powers if p.xmlid == "HKA")


def test_hka_rung_text_is_the_same_whichever_hero_is_active():
    from kirby_cost.core.context import EngineContext

    lad = _loaded("PowerLad")
    ravel = _loaded("Ravel")
    hka = _hka_slot(lad)
    prior = EngineContext.active_hero()
    try:
        EngineContext.set_active_hero(lad)
        own = ([s.display for s in ladder(hka, hero=lad)],
               step_display(hka, hero=lad),
               levels_within(hka, 30, hero=lad).display)
        EngineContext.set_active_hero(ravel)
        other = ([s.display for s in ladder(hka, hero=lad)],
                 step_display(hka, hero=lad),
                 levels_within(hka, 30, hero=lad).display)
        assert EngineContext.active_hero() is ravel     # restored afterwards
    finally:
        EngineContext.set_active_hero(prior)
    assert own == other
    assert "w/STR" in own[1]                          # his own STR, HD's words



# ── Skills and Talents bought in a slot ────────────────────────────────────
# A Multipower slot is normally a power; a character may still hold Skill
# Levels or a Talent there. They have no dice or distance to step through,
# so they are not laddered: the slot is off or as bought. A rung's words
# are HD's column-2 words for the purchase, without its name or
# Limitations, as for a power. The slots are added to a temporary copy of
# PowerLad (one of the bundled own characters) for the test only.

_MP_ID = "1727271632187"   # PowerLad's Multipower


def _slot_xml():
    from lxml import etree
    return [etree.fromstring(x) for x in (
        f'''<TALENT XMLID="LIGHTNING_REFLEXES_ALL" ID="9000000000001" BASECOST="0.0" LEVELS="2" ALIAS="Lightning Reflexes" POSITION="100" MULTIPLIER="1.0" OPTION="ALL" OPTIONID="ALL" OPTION_ALIAS="All Actions" PARENTID="{_MP_ID}" ULTRA_SLOT="Yes" NAME="Talent Slot" />''',
        f'''<SKILL XMLID="COMBAT_LEVELS" ID="9000000000002" BASECOST="0.0" LEVELS="1" ALIAS="Combat Skill Levels" POSITION="101" MULTIPLIER="1.0" OPTION="SINGLE" OPTIONID="SINGLE" OPTION_ALIAS="with Entangle" PARENTID="{_MP_ID}" ULTRA_SLOT="Yes" NAME="Skill Slot" CHARACTERISTIC="GENERAL" FAMILIARITY="No" PROFICIENCY="No"><MODIFIER XMLID="REQUIRESASKILLROLL" ID="9000000000003" BASECOST="-0.5" LEVELS="0" ALIAS="Requires A Roll" POSITION="-1" MULTIPLIER="1.0" OPTION="CHAR" OPTIONID="CHAR" OPTION_ALIAS="DEX roll" /></SKILL>''',
    )]


@pytest.fixture
def slotted(tmp_path):
    """PowerLad with a Talent slot and a Skill Levels slot in his
    Multipower, which is given a Limitation of its own (Costs Endurance)
    so the test sees that the reserve's Limitations stay out of the words."""
    from lxml import etree
    from tests.corpus import require_authored_hdc

    root = etree.parse(str(require_authored_hdc("PowerLad"))).getroot()
    mp = root.find(f".//MULTIPOWER[@ID='{_MP_ID}']")
    mp.append(etree.fromstring(
        '<MODIFIER XMLID="COSTSEND" ID="9000000000004" BASECOST="-0.5" LEVELS="0" '
        'ALIAS="Costs Endurance" POSITION="-1" MULTIPLIER="1.0" OPTION="EVERYPHASE" '
        'OPTIONID="EVERYPHASE" OPTION_ALIAS="Costs END Every Phase" />'))
    powers = root.find("POWERS")
    for el in _slot_xml():
        powers.append(el)
    path = tmp_path / "PowerLad-slotted.hdc"
    path.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
    hero = HDCLoader().load_file(str(path))
    slots = {o.name: o for o in hero.powers
             if getattr(getattr(o, "parent", None), "xmlid", None) == "MULTIPOWER"
             and o.name in ("Talent Slot", "Skill Slot")}
    assert set(slots) == {"Talent Slot", "Skill Slot"}, slots
    return hero, slots


def test_a_talent_in_a_slot_reads_as_hd_writes_it(slotted):
    hero, slots = slotted
    assert step_display(slots["Talent Slot"], hero=hero) == (
        "Lightning Reflexes (+2 DEX to act first with All Actions)")


def test_skill_levels_in_a_slot_read_as_hd_writes_them(slotted):
    hero, slots = slotted
    words = step_display(slots["Skill Slot"], hero=hero)
    assert words == "+1 with Entangle"
    assert "Requires A Roll" not in words and "Skill Slot" not in words
    # Nor the reserve's own Limitation, which the slot is bought under.
    assert "Costs Endurance" not in words and "Active Points" not in words


@pytest.mark.parametrize("name", ["Talent Slot", "Skill Slot"])
def test_skills_and_talents_in_a_slot_are_not_laddered(slotted, name):
    hero, slots = slotted
    with pytest.raises(NotLadderable):
        ladder(slots[name], hero=hero)


def test_words_leave_the_slot_untouched(slotted):
    hero, slots = slotted
    slot = slots["Skill Slot"]
    before = (slot.name, slot.parent, len(slot.assigned_modifiers), slot.column2_output)
    step_display(slot, hero=hero)
    assert (slot.name, slot.parent, len(slot.assigned_modifiers), slot.column2_output) == before


# ── slot_words: what a slot is, to tell it from its neighbours ─────────────
# Two slots can be the same power at the same dice, told apart only by their
# Advantages (one 0 END, one Area Of Effect). `step_display` leaves those
# out on purpose (a rung is dice or metres); `slot_words` is HD's column-2
# words with them kept, and without the slot's name, its Limitations or the
# reserve's. PowerLad's own Multipower supplies the slots, plus two unnamed
# Blasts added to a temporary copy of him.

def _unnamed_blasts():
    from lxml import etree
    mod = ('<MODIFIER XMLID="REDUCEDEND" ID="{id}" BASECOST="0.5" LEVELS="0" ALIAS="Reduced Endurance" '
           'POSITION="-1" MULTIPLIER="1.0" OPTION="ZERO" OPTIONID="ZERO" OPTION_ALIAS="0 END" />')
    lim = ('<MODIFIER XMLID="LIMITEDPOWER" ID="{id}" BASECOST="-1.0" LEVELS="0" ALIAS="Limited Power" '
           'POSITION="-1" MULTIPLIER="1.0" OPTION="HALF" OPTIONID="HALF" '
           'OPTION_ALIAS="Power loses about half of its effectiveness" COMMENTS="test only" />')
    blast = ('<POWER XMLID="ENERGYBLAST" ID="{id}" BASECOST="0.0" LEVELS="6" ALIAS="Blast" POSITION="{pos}" '
             'MULTIPLIER="1.0" INPUT="ED" PARENTID="' + _MP_ID + '" ULTRA_SLOT="Yes" NAME="">{mods}</POWER>')
    return [etree.fromstring(blast.format(id="9000000000011", pos=110,
                                          mods=mod.format(id="9000000000012") + lim.format(id="9000000000013"))),
            etree.fromstring(blast.format(id="9000000000014", pos=111, mods=""))]


@pytest.fixture
def blasts(tmp_path):
    from lxml import etree
    from tests.corpus import require_authored_hdc

    root = etree.parse(str(require_authored_hdc("PowerLad"))).getroot()
    root.find(f".//MULTIPOWER[@ID='{_MP_ID}']").append(etree.fromstring(
        '<MODIFIER XMLID="COSTSEND" ID="9000000000015" BASECOST="-0.5" LEVELS="0" '
        'ALIAS="Costs Endurance" POSITION="-1" MULTIPLIER="1.0" OPTION="EVERYPHASE" '
        'OPTIONID="EVERYPHASE" OPTION_ALIAS="Costs END Every Phase" />'))
    for el in _unnamed_blasts():
        root.find("POWERS").append(el)
    path = tmp_path / "PowerLad-blasts.hdc"
    path.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
    hero = HDCLoader().load_file(str(path))
    by_id = {str(o.id): o for o in hero.powers}
    return hero, by_id


def test_slot_words_drop_the_name_and_the_limitations(blasts):
    hero, by_id = blasts
    assert slot_words(by_id["1727355441687"], hero=hero) == "Entangle 3d6, 6 PD/6 ED"


def test_slot_words_keep_the_advantages(blasts):
    hero, by_id = blasts
    assert slot_words(by_id["9000000000011"], hero=hero) == "Blast 6d6, Reduced Endurance (0 END; +1/2)"


def test_slot_words_tell_two_blasts_apart(blasts):
    hero, by_id = blasts
    assert slot_words(by_id["9000000000014"], hero=hero) == "Blast 6d6"
    assert slot_words(by_id["9000000000011"], hero=hero) != slot_words(by_id["9000000000014"], hero=hero)


def test_slot_words_of_a_characteristic_in_a_slot(blasts):
    hero, by_id = blasts
    assert slot_words(by_id["1727272554833"], hero=hero) == "+45 STR"


def test_slot_words_leave_the_slot_untouched(blasts):
    hero, by_id = blasts
    slot = by_id["9000000000011"]
    before = (slot.name, slot.parent, len(slot.assigned_modifiers), slot.column2_output)
    slot_words(slot, hero=hero)
    assert (slot.name, slot.parent, len(slot.assigned_modifiers), slot.column2_output) == before
