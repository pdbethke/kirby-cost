from tests.corpus import hero_docs_root, require_authored_hdc
import os
from pathlib import Path
import pytest
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.io.build_json import to_build_json, build_from_json

OSE_DIR = Path(os.environ.get(
    "OSE_HDC_DIR",
    str(hero_docs_root() or "/nonexistent")
    + "/Old School Enemies/Old School Enemies HD Files",
))

def _total(h):
    return sum((getattr(o, "real_cost", 0) or 0)
               for attr in ("characteristics", "skills", "perks", "talents", "powers")
               for o in getattr(h, attr, []))

def _ose_files():
    return sorted(OSE_DIR.glob("*.hdc")) if OSE_DIR.exists() else []

@pytest.mark.skipif(not _ose_files(), reason="OSE HDC dir not present")
@pytest.mark.parametrize("hdc", _ose_files(), ids=lambda p: p.stem)
def test_ose_json_roundtrip_is_lossless(hdc):
    ref = HDCLoader().load_file(str(hdc))
    again = build_from_json(to_build_json(ref))
    assert round(_total(again)) == round(_total(ref)), f"{hdc.stem} total drifted"


# ---------------------------------------------------------------------------
# Task 6 additional cases
# ---------------------------------------------------------------------------

from kirby_cost.io.build_cost import cost_build  # noqa: E402

def test_powerlad_str_edit_in_json_recosts():
    doc = to_build_json(HDCLoader().load_file(str(require_authored_hdc("PowerLad"))))
    assert round(cost_build(doc).total_cost) == 400
    for c in doc["characteristics"]:
        if c["xmlid"] == "STR":
            c["levels"] = 90    # 30 -> 90 levels at 1 point each: +60
    assert round(cost_build(doc).total_cost) == 460


def test_fractional_preview_not_prerounded():
    doc = {"name": "T", "template": "Main6E", "base_points": 400, "disad_points": 0,
           "experience": 0, "characteristics": [], "skills": [], "perks": [],
           "talents": [], "disadvantages": [],
           "powers": [{"id": "P1", "xmlid": "ENERGYBLAST", "levels": 5,
                       "modifiers": [{"xmlid": "REQUIRESASKILLROLL", "option_id": "14LESS"}],
                       "adders": []}]}
    r = cost_build(doc)
    assert isinstance(r.total_cost_exact, float)
    assert r.total_cost == int(round(r.total_cost_exact))
    assert r.total_cost_exact == pytest.approx(
        sum(v["real_cost"] for v in r.per_object.values()))


def test_vehicle6e_json_roundtrip(tmp_path):
    from tests.own_copy import vehicle_copy
    ref = HDCLoader().load_file(vehicle_copy(tmp_path))
    again = build_from_json(to_build_json(ref))
    assert round(_total(again)) == round(_total(ref))
