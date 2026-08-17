"""Build-doc round-trip for martial arts (spec 2026-06-07 §2, engine premise)."""
from tests.corpus import hero_docs_root
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.io import to_build_json, build_from_json, extract_costs

CHESHIRE_HDC = Path(
    str(hero_docs_root() or "/nonexistent") + "/Docs/"
    "Champions_Villain_Teams_Character_Pack/Champions Villains 2 6E ƒ/"
    "GRAB/CHESHIRE_CAT-CV2.hdc"
)

pytestmark = pytest.mark.skipif(
    not CHESHIRE_HDC.exists(), reason="machine-bound HDC corpus not present"
)


def _load():
    return HDCLoader().load_file(str(CHESHIRE_HDC))


def test_build_doc_emits_martial_arts():
    doc = to_build_json(_load())
    assert "martial_arts" in doc
    maneuvers = [o for o in doc["martial_arts"] if o["xmlid"] == "MANEUVER"]
    assert len(maneuvers) == 7
    dodge = next(o for o in maneuvers if o.get("alias") == "Martial Dodge")
    assert dodge["maneuver"] is True
    assert dodge["ocv"] == "--" and dodge["dcv"] == "+5"
    assert dodge["phase"] == "1/2" and dodge["add_str"] is False
    extradc = [o for o in doc["martial_arts"] if o["xmlid"] == "EXTRADC"]
    assert len(extradc) == 1 and extradc[0]["levels"] == 2


def test_build_doc_round_trips_martial_arts_with_costs():
    loaded = _load()
    doc = to_build_json(loaded)
    rebuilt = build_from_json(doc)
    from kirby_cost.objects.martial_arts.maneuver import Maneuver
    orig = [m for m in loaded.martial_arts if isinstance(m, Maneuver)]
    back = [m for m in rebuilt.martial_arts if isinstance(m, Maneuver)]
    assert len(back) == len(orig) == 7
    for o, b in zip(orig, back):
        assert b.display == o.display
        assert b.real_cost_pre_list == o.real_cost_pre_list
        assert (b.ocv, b.dcv, b.phase, b.dc, b.add_str, b.use_weapon,
                b.damage_type, b.max_str, b.str_multiplier, b.category) == \
               (o.ocv, o.dcv, o.phase, o.dc, o.add_str, o.use_weapon,
                o.damage_type, o.max_str, o.str_multiplier, o.category)
    # The martial_arts section round-trips perfectly (all 7 maneuvers + their
    # per-maneuver costs match).
    orig_ma_cost = sum(getattr(m, "real_cost", 0) or 0 for m in loaded.martial_arts)
    back_ma_cost = sum(getattr(m, "real_cost", 0) or 0 for m in rebuilt.martial_arts)
    assert back_ma_cost == orig_ma_cost
    # The -3 gap on total_points that existed in v0.1.10 was caused by the
    # TRIGGER/RESET adder explicit BASECOST=0.0 being dropped (truthiness bug).
    # Fixed in fix(build-doc) commit — provenance flag gates emission instead.
    assert rebuilt.total_points == loaded.total_points == 574.0


def test_extract_costs_includes_maneuvers():
    loaded = _load()
    costs = extract_costs(loaded)
    assert costs.points_spent == loaded.total_points
    doc = to_build_json(loaded)
    ma_ids = {o["id"] for o in doc["martial_arts"] if "id" in o}
    assert ma_ids and ma_ids.issubset(set(costs.per_object.keys()))
