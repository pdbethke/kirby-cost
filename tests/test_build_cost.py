import copy
import pytest
from kirby_cost.io.build_cost import cost_build, CostResult, extract_costs
from kirby_cost.io.build_json import build_from_json, to_build_json

MINIMAL = {
    "name": "Brick", "template": "Main6E",
    "base_points": 400, "disad_points": 75, "experience": 0,
    "characteristics": [{"xmlid": "STR", "levels": 30, "id": "C1"}],
    "powers": [], "skills": [], "perks": [], "talents": [], "disadvantages": [],
}

def test_cost_build_reports_total_and_subcost():
    r = cost_build(MINIMAL)
    assert isinstance(r, CostResult)
    assert round(r.total_cost) == 30
    assert r.total_cost_exact == pytest.approx(30.0)
    assert r.base_points == 400 and r.disad_points == 75
    assert any(round(v["real_cost"]) == 30 for v in r.per_object.values())

def test_cost_build_str_edit_changes_total():
    doc = copy.deepcopy(MINIMAL)
    doc["characteristics"][0]["levels"] = 90   # STR -> 100
    r = cost_build(doc)
    assert round(r.total_cost) == 90

def test_per_object_ids_join_to_build_doc_ids():
    """Fix 1: per_object O{n} keys must be the same ids that to_build_json emits.

    Build a doc with at least one characteristic, one power, AND one skill so
    the numbering diverges if the two iteration orders differ. After the fix both
    _SECTION_TAG (build_json) and _BUILD_LISTS (build_cost) iterate in the same
    order (characteristics -> powers -> skills -> perks -> talents), so O2 in the
    doc is the power, and O2 in per_object is also the power.
    """
    doc = {
        "name": "JoinTest", "template": "Main6E",
        "base_points": 400, "disad_points": 75, "experience": 0,
        "characteristics": [{"xmlid": "STR", "levels": 10}],
        "powers": [{"xmlid": "ENERGYBLAST", "levels": 5, "input": "ED"}],
        "skills": [{"xmlid": "ACROBATICS"}],
        "perks": [], "talents": [], "disadvantages": [],
    }
    hero = build_from_json(doc)
    doc2 = to_build_json(hero)
    r = extract_costs(hero)

    # Locate the power entry in the emitted doc and read its id.
    power_entries = doc2.get("powers", [])
    assert len(power_entries) == 1, "expected exactly one power in emitted doc"
    power_doc_id = power_entries[0]["id"]   # e.g. "O2"

    # That id must be a key in per_object (the join works).
    assert power_doc_id in r.per_object, (
        f"per_object missing key '{power_doc_id}' — id mismatch between "
        f"to_build_json and extract_costs; per_object keys: {list(r.per_object)}"
    )

    # And the real_cost stored there must equal the power's own real_cost.
    expected_rc = float(hero.powers[0].real_cost)
    assert r.per_object[power_doc_id]["real_cost"] == pytest.approx(expected_rc), (
        f"per_object['{power_doc_id}']['real_cost'] = "
        f"{r.per_object[power_doc_id]['real_cost']} != {expected_rc}"
    )


def test_extract_costs_recosts_a_prebuilt_hero():
    """build-once-recost-many: build the loaded build once, mutate it in memory,
    recost via extract_costs WITHOUT rebuilding from the doc."""
    from kirby_cost.io.build_json import build_from_json
    from kirby_cost.io.build_cost import extract_costs
    hero = build_from_json(MINIMAL)
    r1 = extract_costs(hero)
    strc = [c for c in hero.characteristics if c.xmlid == "STR"][0]
    strc.levels = 90
    hero.compute_characteristic_values()  # refreshes internal characteristic-value cache that downstream cost properties read after mutating levels
    r2 = extract_costs(hero)
    assert round(r1.total_cost) == 30 and round(r2.total_cost) == 90
