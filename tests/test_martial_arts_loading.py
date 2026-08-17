"""MARTIALARTS section loading — engine side (spec 2026-06-07 §1)."""
from tests.corpus import hero_docs_root
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

CHESHIRE_HDC = Path(
    str(hero_docs_root() or "/nonexistent") + "/Docs/"
    "Champions_Villain_Teams_Character_Pack/Champions Villains 2 6E ƒ/"
    "GRAB/CHESHIRE_CAT-CV2.hdc"
)
GORGON_HDC = Path(
    str(hero_docs_root() or "/nonexistent") + "/Docs/"
    "CV1HDFiles/CV1 HD Files ƒ/KING_COBRA/GORGON-CV1.hdc"
)


def skip_if_hdc_missing():
    if not CHESHIRE_HDC.exists() or not GORGON_HDC.exists():
        pytest.skip("Machine-bound HDC corpus not present on this host")


def test_maneuver_is_registered():
    from kirby_cost.objects.martial_arts.maneuver import Maneuver
    loader = HDCLoader()
    obj = loader._create_instance("MANEUVER", "power")
    assert isinstance(obj, Maneuver)


def test_cheshire_maneuvers_loaded():
    skip_if_hdc_missing()
    hero = HDCLoader().load_file(str(CHESHIRE_HDC))
    from kirby_cost.objects.martial_arts.maneuver import Maneuver
    maneuvers = [m for m in hero.martial_arts if isinstance(m, Maneuver)]
    assert len(maneuvers) == 7  # actual count in CHESHIRE_CAT-CV2.hdc (spec said 15, file has 7)

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


def test_loader_sets_active_hero_with_maneuver_contract():
    skip_if_hdc_missing()
    from kirby_cost.core.context import EngineContext
    hero = HDCLoader().load_file(str(CHESHIRE_HDC))
    active = EngineContext.active_hero()
    assert active is hero
    # The three things Maneuver cost math dereferences:
    assert active.maneuvers is hero.martial_arts
    str_char = active.characteristic(1)
    assert str_char is not None and str_char.xmlid == "STR"
    assert active.rules is not None


def test_characteristic_lookup_uses_java_constants():
    skip_if_hdc_missing()
    hero = HDCLoader().load_file(str(CHESHIRE_HDC))
    # Java Constants contract: INT is 5, EGO is 6, SPD is 11, OCV is 30.
    # Verified present on Cheshire: STR DEX CON INT EGO PRE OCV DCV OMCV DMCV
    #   SPD PD ED REC END BODY STUN RUNNING SWIMMING LEAPING
    assert hero.characteristic(5).xmlid == "INT"
    assert hero.characteristic(6).xmlid == "EGO"
    assert hero.characteristic(11).xmlid == "SPD"
    assert hero.characteristic(30).xmlid == "OCV"
    assert hero.characteristic(9999) is None


def test_totals_include_martial_arts():
    skip_if_hdc_missing()
    hero = HDCLoader().load_file(str(CHESHIRE_HDC))
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
    skip_if_hdc_missing()
    cheshire = HDCLoader().load_file(str(CHESHIRE_HDC))
    assert "MARTIALARTS" not in cheshire.unparsed_sections

    gorgon = HDCLoader().load_file(str(GORGON_HDC))
    assert "EQUIPMENT" not in gorgon.unparsed_sections, "EQUIPMENT is parsed now"

    # A tag the loader genuinely does not know must still be reported.
    src = Path(GORGON_HDC).read_text(encoding="utf-8", errors="ignore")
    doctored = src.replace("</CHARACTER>", "<SPACESHIP_BAY/></CHARACTER>", 1)
    p = tmp_path / "doctored.hdc"
    p.write_text(doctored, encoding="utf-8")
    assert "SPACESHIP_BAY" in HDCLoader().load_file(str(p)).unparsed_sections


def test_martial_arts_list_builds_as_real_list():
    skip_if_hdc_missing()
    hero = HDCLoader().load_file(str(CHESHIRE_HDC))
    from kirby_cost.objects.list import List as HDList
    lists = [o for o in hero.martial_arts if isinstance(o, HDList)]
    assert len(lists) == 1
    assert lists[0].alias == "Aikijutsu"


FIREWING_HDC = Path(
    str(hero_docs_root() or "/nonexistent") + "/Old School Enemies/"
    "Old School Enemies HD Files/Firewing.hdc"
)


def test_skills_list_container_costs_zero():
    # Java builds SKILLS-section LIST containers as real List (real_cost 0.0);
    # the old _FallbackObject path cost them 1.0 (oracle corpus: unanimous 0.0).
    if not FIREWING_HDC.exists():
        pytest.skip("Firewing HDC not present")
    hero = HDCLoader().load_file(str(FIREWING_HDC))
    from kirby_cost.objects.list import List as HDList
    skill_lists = [o for o in hero.skills if isinstance(o, HDList)]
    assert skill_lists, "expected at least one LIST container in SKILLS"
    assert all(lst.real_cost == 0.0 for lst in skill_lists)


def test_maneuvers_link_to_style_list():
    skip_if_hdc_missing()
    hero = HDCLoader().load_file(str(CHESHIRE_HDC))
    from kirby_cost.objects.martial_arts.maneuver import Maneuver
    maneuvers = [m for m in hero.martial_arts if isinstance(m, Maneuver)]
    linked = [m for m in maneuvers if m.parent is not None]
    # All 7 of Cheshire's maneuvers carry PARENTID pointing at the Aikijutsu list
    assert len(linked) == 7
    assert all(m.parent.alias == "Aikijutsu" for m in linked)
