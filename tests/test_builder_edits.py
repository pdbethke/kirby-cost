"""The builder's first layer: edits on a build doc, costed by the engine.

Two-databases spec §4a. One function, two callers:

* a CAMPAIGN keeps a character's base in the codex and stores only its own
  changes (versions keyed by HD's ``ID``), and blends them over the base;
* an AI builds NPCs, bases and equipment (Peter, 2026-11-24: "the ai needs
  to be able to build npcs, encounters, bases, equipment - everything") by
  proposing the same edits, which the engine applies and costs.

The doc is the CURATED build doc (`to_build_json`), the shape a relational
store keeps, so an edit's payload is one purchase's rows (Peter,
2026-11-25). An edit names its target by HD's own ``ID`` (it survives a
re-import).
Anything that does not fit the base is REFUSED by name, never patched over
(`EditConflict`): a replace or remove of an ID the base lacks, an add whose
ID is already taken or whose ``parent`` names nothing. The base doc is
never changed; `apply` returns a new one, which `build_from_json` then costs.
"""
from __future__ import annotations

import copy

import pytest

from kirby_cost.builder import Add, EditConflict, Remove, Replace, Section, apply
from kirby_cost.io.build_json import build_from_json, to_build_json
from kirby_cost.io.formats import load_build
from tests.corpus import require_authored_hdc

STR_ID = "1648344749637"
DEDUCTION_ID = "1648355382902"
MULTIPOWER_ID = "1648348957819"
BRAIN_POKE_ID = "1787052005008"        # a slot in that Multipower


@pytest.fixture(scope="module")
def ravel():
    return to_build_json(load_build(str(require_authored_hdc("Ravel")), format="hdc"))


def _total(doc) -> float:
    return build_from_json(doc).total_points


def _find(doc, hd_id):
    for key, objs in doc.items():
        if isinstance(objs, list):
            for obj in objs:
                if obj.get("id") == hd_id:
                    return obj
    return None


def _node(doc, hd_id):
    return copy.deepcopy(_find(doc, hd_id))


def _fresh(obj, top_id):
    """A copy under a new id, as any new purchase has."""
    out = copy.deepcopy(obj)
    out["id"] = top_id
    return out


# ---- the three edits ------------------------------------------------------

def test_no_edits_is_the_base(ravel):
    assert _total(apply(ravel, [])) == _total(ravel)


def test_replace_raises_strength_and_the_engine_prices_it(ravel):
    stronger = _node(ravel, STR_ID)
    stronger["levels"] = 10
    out = apply(ravel, [Replace(STR_ID, stronger)])
    assert _find(out, STR_ID)["levels"] == 10
    assert _total(out) == _total(ravel) + 10      # STR is 1 point a level (6E1 p.37)


def test_add_buys_a_skill(ravel):
    second = _node(ravel, DEDUCTION_ID)
    second["id"] = "9000000000001"
    second["xmlid"] = "CONCEALMENT"
    second["alias"] = "Concealment"
    out = apply(ravel, [Add(Section.SKILLS, second)])
    assert _find(out, "9000000000001") is not None
    assert _total(out) > _total(ravel)


def test_remove_sells_a_skill_back(ravel):
    out = apply(ravel, [Remove(DEDUCTION_ID)])
    assert _find(out, DEDUCTION_ID) is None
    assert _total(out) < _total(ravel)


def test_edits_apply_in_order(ravel):
    """An add may be replaced by a later edit in the same list."""
    second = _node(ravel, DEDUCTION_ID)
    second["id"] = "9000000000002"
    better = copy.deepcopy(second)
    better["levels"] = 2
    out = apply(ravel, [Add(Section.SKILLS, second), Replace("9000000000002", better)])
    assert _find(out, "9000000000002")["levels"] == 2


def test_the_base_is_never_changed(ravel):
    before = copy.deepcopy(ravel)
    stronger = _node(ravel, STR_ID)
    stronger["levels"] = 10
    apply(ravel, [Replace(STR_ID, stronger), Remove(DEDUCTION_ID)])
    assert ravel == before


# ---- refused, by name -----------------------------------------------------

def test_replacing_an_id_the_base_lacks_is_refused(ravel):
    ghost = _node(ravel, STR_ID)
    ghost["id"] = "404"
    with pytest.raises(EditConflict, match="404"):
        apply(ravel, [Replace("404", ghost)])


def test_a_replacement_keeps_its_identity(ravel):
    other = _node(ravel, STR_ID)
    other["id"] = "123"
    with pytest.raises(EditConflict, match="keeps"):
        apply(ravel, [Replace(STR_ID, other)])


def test_removing_an_id_the_base_lacks_is_refused(ravel):
    with pytest.raises(EditConflict, match="404"):
        apply(ravel, [Remove("404")])


def test_adding_an_id_already_taken_is_refused(ravel):
    with pytest.raises(EditConflict, match=DEDUCTION_ID):
        apply(ravel, [Add(Section.SKILLS, _node(ravel, DEDUCTION_ID))])


def test_a_section_is_a_section_not_a_string(ravel):
    second = _node(ravel, DEDUCTION_ID)
    second["id"] = "9000000000003"
    with pytest.raises(TypeError, match="SKILLS"):
        apply(ravel, [Add("SKILLS", second)])


def test_a_purchase_without_an_id_is_refused(ravel):
    second = _node(ravel, DEDUCTION_ID)
    del second["id"]
    with pytest.raises(EditConflict, match="no ID"):
        apply(ravel, [Add(Section.SKILLS, second)])


def test_a_slot_must_name_a_framework_that_exists(ravel):
    slot = _fresh(_node(ravel, BRAIN_POKE_ID), "9000000000004")
    slot["parent"] = "nowhere"
    with pytest.raises(EditConflict, match="nowhere"):
        apply(ravel, [Add(Section.POWERS, slot)])


def test_a_slot_may_be_added_to_an_existing_framework(ravel):
    slot = _fresh(_node(ravel, BRAIN_POKE_ID), "9000000000005")
    out = apply(ravel, [Add(Section.POWERS, slot)])
    assert _find(out, "9000000000005")["parent"] == MULTIPOWER_ID
    hero = build_from_json(out)
    (slot,) = [p for p in hero.powers if str(p.id) == "9000000000005"]
    assert str(slot.parent.id) == MULTIPOWER_ID      # it is in the framework


def test_removing_a_framework_with_slots_still_in_it_is_refused(ravel):
    with pytest.raises(EditConflict, match=BRAIN_POKE_ID):
        apply(ravel, [Remove(MULTIPOWER_ID)])


def test_a_store_round_trip_keeps_the_edit(ravel):
    """What a store does: blend, cost, write the curated doc back out. The
    edited purchase comes back the same purchase, under the same id."""
    stronger = _node(ravel, STR_ID)
    stronger["levels"] = 10
    out = apply(ravel, [Replace(STR_ID, stronger), Remove(DEDUCTION_ID)])
    again = to_build_json(build_from_json(out))
    assert _find(again, STR_ID)["levels"] == 10
    assert _find(again, DEDUCTION_ID) is None
    assert _total(again) == _total(out)
