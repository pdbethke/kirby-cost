"""MARTIALARTS section loading — engine side (spec 2026-06-07 §1)."""
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.corpus import require_authored_hdc
from tests.own_copy import MARTIAL_DODGE, EXTRA_DC_2, own_copy

# Ravel owns two maneuvers. The copy adds a style LIST ("Aikijutsu"), Martial
# Dodge filed under it, and +2 HTH damage classes.
_STYLE = (
    '<LIST XMLID="GENERIC_OBJECT" ID="9000000000090" BASECOST="0.0" LEVELS="0" '
    'ALIAS="Aikijutsu" POSITION="9" MULTIPLIER="1.0" NAME="Aikijutsu" />')
_DODGE_IN_STYLE = MARTIAL_DODGE.replace(
    'POSITION="2"', 'POSITION="2" PARENTID="9000000000090"')
_SKILL_GROUP = (
    '<LIST XMLID="GENERIC_OBJECT" ID="9000000000091" BASECOST="0.0" LEVELS="0" '
    'ALIAS="Skill Group" POSITION="9" MULTIPLIER="1.0" NAME="Skill Group" />')


@pytest.fixture
def stylist(tmp_path):
    """Ravel plus a martial-arts style list, Martial Dodge under it, EXTRADC."""
    return HDCLoader().load_file(own_copy(
        tmp_path, "Ravel",
        section_xml=[("MARTIALARTS", _STYLE), ("MARTIALARTS", _DODGE_IN_STYLE),
                     ("MARTIALARTS", EXTRA_DC_2)],
        filename="Ravel-style.hdc"))


def test_maneuver_is_registered():
    from kirby_cost.objects.martial_arts.maneuver import Maneuver
    loader = HDCLoader()
    obj = loader._create_instance("MANEUVER", "power")
    assert isinstance(obj, Maneuver)


def test_maneuvers_loaded(stylist):
    hero = stylist
    from kirby_cost.objects.martial_arts.maneuver import Maneuver
    maneuvers = [m for m in hero.martial_arts if isinstance(m, Maneuver)]
    assert len(maneuvers) == 3  # Ravel's two plus Martial Dodge

    dodge = next((m for m in maneuvers if m.display == "Martial Dodge"), None)
    assert dodge is not None, (
        f"'Martial Dodge' not found; maneuvers present: {[m.display for m in maneuvers]}"
    )
    assert dodge.ocv == "--"
    assert dodge.dcv == "+5"
    assert dodge.phase == "1/2"
    assert dodge.add_str is False
    assert dodge.real_cost_pre_list == 4.0  # BASECOST, no modifiers

    # EXTRADC rides in the same flat list, Java-style
    from kirby_cost.objects.martial_arts.extra_damage_classes import ExtraDamageClasses
    extradc = [m for m in hero.martial_arts if isinstance(m, ExtraDamageClasses)]
    assert len(extradc) == 1
    assert extradc[0].levels == 2


def test_loader_sets_active_hero_with_maneuver_contract(stylist):
    from kirby_cost.core.context import EngineContext
    hero = stylist
    active = EngineContext.active_hero()
    assert active is hero
    # The three things Maneuver cost math dereferences:
    assert active.maneuvers is hero.martial_arts
    str_char = active.characteristic(1)
    assert str_char is not None and str_char.xmlid == "STR"
    assert active.rules is not None


def test_characteristic_lookup_uses_java_constants(stylist):
    hero = stylist
    # Java Constants contract: INT is 5, EGO is 6, SPD is 11, OCV is 30.
    # Verified present on Ravel: STR DEX CON INT EGO PRE OCV DCV OMCV DMCV
    #   SPD PD ED REC END BODY STUN RUNNING SWIMMING LEAPING
    assert hero.characteristic(5).xmlid == "INT"
    assert hero.characteristic(6).xmlid == "EGO"
    assert hero.characteristic(11).xmlid == "SPD"
    assert hero.characteristic(30).xmlid == "OCV"
    assert hero.characteristic(9999) is None


def test_totals_include_martial_arts(stylist):
    hero = stylist
    ma_points = sum(m.real_cost for m in hero.martial_arts)
    assert ma_points > 0
    expected = sum(
        sum(o.real_cost for o in lst)
        for lst in (hero.characteristics, hero.skills, hero.perks,
                    hero.talents, hero.martial_arts, hero.powers)
    )
    assert hero.total_points == expected
    assert hero.available_points == (
        hero.base_points + hero.disads_used + hero.experience - hero.total_points
    )


def test_unparsed_sections_visible(tmp_path):
    """The mechanism that made the MARTIALARTS gap findable.

    This used EQUIPMENT as its worked example of a skipped section. EQUIPMENT
    is now parsed too (see test_equipment_loading.py), so the example moved to
    a synthetic unknown tag -- the point of the test is the reporting
    mechanism, not which section happens to be missing this month.
    """
    ravel = HDCLoader().load_file(str(require_authored_hdc("Ravel")))
    assert "MARTIALARTS" not in ravel.unparsed_sections
    assert "EQUIPMENT" not in ravel.unparsed_sections, "EQUIPMENT is parsed now"

    # A tag the loader genuinely does not know must still be reported.
    src = Path(require_authored_hdc("Ravel")).read_bytes().decode("utf-16")
    doctored = src.replace("</CHARACTER>", "<SPACESHIP_BAY/></CHARACTER>", 1)
    p = tmp_path / "doctored.hdc"
    p.write_text(doctored, encoding="utf-8")
    assert "SPACESHIP_BAY" in HDCLoader().load_file(str(p)).unparsed_sections


def test_martial_arts_list_builds_as_real_list(stylist):
    hero = stylist
    from kirby_cost.objects.list import List as HDList
    lists = [o for o in hero.martial_arts if isinstance(o, HDList)]
    assert len(lists) == 1
    assert lists[0].alias == "Aikijutsu"


def test_skills_list_container_costs_zero(tmp_path):
    # Java builds SKILLS-section LIST containers as real List (real_cost 0.0);
    # the old _FallbackObject path cost them 1.0 (oracle corpus: unanimous 0.0).
    hero = HDCLoader().load_file(own_copy(
        tmp_path, section_xml=[("SKILLS", _SKILL_GROUP)]))
    from kirby_cost.objects.list import List as HDList
    skill_lists = [o for o in hero.skills if isinstance(o, HDList)]
    assert skill_lists, "expected at least one LIST container in SKILLS"
    assert all(lst.real_cost == 0.0 for lst in skill_lists)


def test_maneuvers_link_to_style_list(stylist):
    hero = stylist
    from kirby_cost.objects.martial_arts.maneuver import Maneuver
    maneuvers = [m for m in hero.martial_arts if isinstance(m, Maneuver)]
    linked = [m for m in maneuvers if m.parent is not None]
    # Martial Dodge carries PARENTID pointing at the Aikijutsu list; Ravel's own
    # two maneuvers are filed under no style
    assert len(linked) == 1
    assert all(m.parent.alias == "Aikijutsu" for m in linked)
