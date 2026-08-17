from tests.corpus import corpus_root, hero_docs_root
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

FIREWING = OSE_DIR / "Firewing.hdc"

@pytest.mark.skipif(not FIREWING.exists(), reason="Firewing not present")
def test_firewing_str_edit_in_json_recosts_to_819():
    doc = to_build_json(HDCLoader().load_file(str(FIREWING)))
    for c in doc["characteristics"]:
        if c["xmlid"] == "STR":
            c["levels"] = 90    # STR base 10 + 90 = 100
    assert round(cost_build(doc).total_cost) == 818


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


VEHICLE = (corpus_root() or Path("/nonexistent")) / "villains/CV1HDFiles/CV1 HD Files ƒ/WARLORD/WARLORD_-_THE_FLYING_FORTRESS-CV1.hdc"

@pytest.mark.skipif(not VEHICLE.exists(), reason="no Vehicle6E HDC provided")
def test_vehicle6e_json_roundtrip():
    ref = HDCLoader().load_file(str(VEHICLE))
    again = build_from_json(to_build_json(ref))
    assert round(_total(again)) == round(_total(ref))
