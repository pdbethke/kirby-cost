"""Loading the HDC <EQUIPMENT> section.

Spec: kirby/docs/superpowers/specs/2026-08-05-equipment-section-loading-design.md

`_KNOWN_SECTIONS` omitted EQUIPMENT, so 60 of the 103 Equipment Guide prefabs
parsed to ZERO objects and dropped their gear -- every modern pistol, sword
and rifle in the book -- into `unparsed_sections`. Same omission, same silent
failure mode as MARTIALARTS: the data is right, the consumer is missing, and
nothing fails loudly.
"""
from __future__ import annotations
from tests.corpus import hero_docs_root

import glob
import os

import pytest

from kirby_cost.io.hdc_loader import HDCLoader, _KNOWN_SECTIONS

HSEG = str(hero_docs_root() or "/nonexistent") + "/Docs/6E_HSEG_HD/HSEG HD Files"


def _prefab(stem: str) -> str:
    hits = glob.glob(f"{HSEG}/**/{stem}.hdp", recursive=True)
    if not hits:
        pytest.skip(f"HSEG prefab not available: {stem}")
    return hits[0]


def test_equipment_is_a_known_section() -> None:
    assert "EQUIPMENT" in _KNOWN_SECTIONS


def test_gear_in_the_equipment_section_actually_loads() -> None:
    """Before the fix this file loaded to nothing at all."""
    hero = HDCLoader().load_file(_prefab("MODERN_SEMI-AUTOMATIC_PISTOLS-HSEG"))
    assert len(hero.equipment) == 83
    names = {getattr(o, "name", "") for o in hero.equipment}
    assert "AA Arms AP9" in names


def test_equipment_no_longer_reported_as_unparsed() -> None:
    hero = HDCLoader().load_file(_prefab("MODERN_SEMI-AUTOMATIC_PISTOLS-HSEG"))
    assert "EQUIPMENT" not in hero.unparsed_sections


def test_equipment_is_costed_by_the_engine() -> None:
    """Gear has a Real Cost even though the character does not pay it
    (6E2 p182: equipment is built with Character Points). Costs come FROM
    the engine per object -- never hand-rolled."""
    hero = HDCLoader().load_file(_prefab("MODERN_SEMI-AUTOMATIC_PISTOLS-HSEG"))
    assert sum(o.real_cost for o in hero.equipment) == 783.0


def test_equipment_does_not_leak_into_total_points() -> None:
    """THE guard.

    HD's Equipment tab is by definition for gear "that does not cost
    Character Points" (Hero Designer Documentation p14); 6E1 p34 says the
    same for Heroic campaigns. So equipment must load into its own list and
    leave the character's spent points exactly where they were.

    Asserted structurally rather than against a magic number: total_points is
    the Java meta loop (chars+skills+perks+talents+maneuvers+powers) and must
    equal that sum with no equipment term, even though equipment is non-empty
    and non-free.
    """
    hero = HDCLoader().load_file(_prefab("MODERN_SEMI-AUTOMATIC_PISTOLS-HSEG"))
    assert hero.equipment, "equipment must have loaded for this test to mean anything"
    assert sum(o.real_cost for o in hero.equipment) > 0, "and must not be free"

    expected = sum(
        o.real_cost
        for lst in (hero.characteristics, hero.skills, hero.perks,
                    hero.talents, hero.martial_arts, hero.powers)
        for o in lst
    )
    assert hero.total_points == expected


_GEAR = (
    '<POWER XMLID="HANDTOHANDATTACK" ID="9000000000110" BASECOST="0.0" LEVELS="4" '
    'ALIAS="Hand-To-Hand Attack" POSITION="0" MULTIPLIER="1.0" NAME="Probe Cudgel" '
    'QUANTITY="1" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes" INPUT="STR" />')


def test_a_character_with_equipment_keeps_its_total(tmp_path) -> None:
    """A character whose <EQUIPMENT> section is non-empty. Loading the gear
    must not move a single point: PowerLad's total is the same with a piece of
    gear in his Equipment section as without it."""
    from tests.corpus import require_authored_hdc
    from tests.own_copy import own_copy
    plain = HDCLoader().load_file(str(require_authored_hdc("PowerLad")))
    hero = HDCLoader().load_file(
        own_copy(tmp_path, section_xml=[("EQUIPMENT", _GEAR)]))
    assert hero.equipment, "the EQUIPMENT section must load"
    assert len(hero.powers) == len(plain.powers), "powers must be untouched by the section"
    expected = sum(
        o.real_cost
        for lst in (hero.characteristics, hero.skills, hero.perks,
                    hero.talents, hero.martial_arts, hero.powers)
        for o in lst
    )
    assert hero.total_points == expected == plain.total_points


def test_a_prefab_with_gear_in_POWERS_is_unaffected() -> None:
    """The 43 prefabs that already worked must not change."""
    hero = HDCLoader().load_file(_prefab("MELEE_WEAPONS-HSEG"))
    assert len(hero.powers) == 165
    assert hero.equipment == []


def test_powers_section_still_defaults_to_POWERS() -> None:
    """Regression: parameterising _load_powers_section must not change its
    default. BLASTERS keeps its gear in <POWERS>, so a default-arg call has
    to still find all 214."""
    hero = HDCLoader().load_file(_prefab("BLASTERS-HSEG"))
    assert len(hero.powers) == 214


def test_every_prefab_loads_and_the_dropped_gear_comes_back() -> None:
    files = sorted(glob.glob(f"{HSEG}/**/*.hdp", recursive=True))
    if not files:
        pytest.skip("HSEG prefabs not available")
    assert len(files) == 103
    powers = equipment = 0
    for f in files:
        h = HDCLoader().load_file(f)
        powers += len(h.powers)
        equipment += len(h.equipment)
    # 2,795 were always loadable via <POWERS>; 1,081 top-level gear items
    # were being dropped from <EQUIPMENT> and now come back.
    assert powers == 2795
    assert equipment == 1081
