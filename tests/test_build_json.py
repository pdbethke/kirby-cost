from tests.corpus import hero_docs_root
import pytest
from pathlib import Path
from kirby_cost.io.build_json import build_from_json, BuildDocError

MINIMAL = {
    "name": "Brick", "template": "Main6E",
    "base_points": 400, "disad_points": 75, "experience": 0,
    "characteristics": [{"xmlid": "STR", "levels": 30}],
    "powers": [], "skills": [], "perks": [], "talents": [], "disadvantages": [],
}

def test_build_from_json_costs_a_characteristic():
    hero = build_from_json(MINIMAL)
    strs = [c for c in hero.characteristics if c.xmlid == "STR"]
    assert len(strs) == 1
    assert hero.characteristic_value("STR") == 40   # base 10 + 30
    assert round(strs[0].real_cost) == 30           # 6E STR = 1/pt

def test_build_from_json_nested_modifier_reduces_cost():
    doc = dict(MINIMAL, powers=[{
        "id": "P1", "xmlid": "ENERGYBLAST", "levels": 10, "input": "ED",
        "modifiers": [{"xmlid": "REQUIRESASKILLROLL", "option_id": "14LESS", "levels": 0}],
        "adders": [],
    }])
    hero = build_from_json(doc)
    eb = [p for p in hero.powers if p.xmlid == "ENERGYBLAST"][0]
    assert eb.active_cost > eb.real_cost   # a limitation reduced real below active

def test_build_from_json_rejects_missing_xmlid():
    bad = dict(MINIMAL, characteristics=[{"levels": 5}])
    with pytest.raises(BuildDocError):
        build_from_json(bad)


# ── Task 4: to_build_json tests ──────────────────────────────────────────────

from kirby_cost.io.build_json import to_build_json
from kirby_cost.io.hdc_loader import HDCLoader

FIREWING = (hero_docs_root() or Path("/nonexistent")) / "Old School Enemies/Old School Enemies HD Files/Firewing.hdc"


def _total(h):
    return sum((getattr(o, "real_cost", 0) or 0)
               for attr in ("characteristics", "skills", "perks", "talents", "powers")
               for o in getattr(h, attr, []))


def test_to_build_json_shape():
    hero = build_from_json(MINIMAL)
    doc = to_build_json(hero)
    assert doc["name"] == "Brick"
    assert doc["base_points"] == 400
    assert {"xmlid": "STR", "levels": 30} == {k: doc["characteristics"][0][k]
                                              for k in ("xmlid", "levels")}


@pytest.mark.skipif(not FIREWING.exists(), reason="Firewing HDC not present")
def test_firewing_json_roundtrip_is_lossless():
    ref = HDCLoader().load_file(str(FIREWING))
    again = build_from_json(to_build_json(ref))
    assert round(_total(again)) == round(_total(ref)) == 758


# ── Sub-power round-trip (synthetic, not relying on the OSE corpus) ──────────

def _compound_doc():
    """A CompoundPower with two sub-powers (no OSE file needed)."""
    return dict(
        MINIMAL,
        powers=[{
            "id": "P1", "xmlid": "COMPOUNDPOWER", "alias": "Compound",
            "sub_powers": [
                {"xmlid": "ENERGYBLAST", "levels": 5, "input": "ED"},
                {"xmlid": "ENERGYBLAST", "levels": 4, "input": "PD"},
            ],
        }],
    )


def test_compound_subpowers_build_with_nonzero_cost():
    # CompoundPower.total_cost = sum of its sub-powers, so the children MUST
    # be rebuilt or the compound costs 0.
    hero = build_from_json(_compound_doc())
    cp = [p for p in hero.powers if p.xmlid == "COMPOUNDPOWER"][0]
    assert len(cp.powers) == 2
    assert all(round(s.real_cost) > 0 for s in cp.powers)
    assert round(cp.real_cost) == 45   # 5 dice ED (25) + 4 dice PD (20)


def test_to_build_json_emits_subpowers_and_roundtrips():
    hero = build_from_json(_compound_doc())
    doc = to_build_json(hero)
    cp = [o for o in doc["powers"] if o["xmlid"] == "COMPOUNDPOWER"][0]
    # to_build_json must emit the sub-powers (the old code dropped them).
    assert len(cp["sub_powers"]) == 2
    assert [sp["xmlid"] for sp in cp["sub_powers"]] == ["ENERGYBLAST", "ENERGYBLAST"]
    # ...and re-reading them rebuilds the compound with its full cost.
    again = build_from_json(doc)
    cp2 = [p for p in again.powers if p.xmlid == "COMPOUNDPOWER"][0]
    assert len(cp2.powers) == 2
    assert round(cp2.real_cost) == 45


def test_user_wording_and_notes_survive_the_build_doc():
    """TEXT is the user's own words, and the build doc used to eat them.

    HD stores TEXT only when the user has typed over the display string it
    would generate — ``setTextOutput`` stores null when the text matches
    ``getColumn2Output()``, and ``getSaveXML`` writes the attribute only when
    something is stored (GenericObject.java:1884, :1916). So TEXT in a
    document is never incidental: it is the one place a character carries
    wording HD did not produce, and 117 objects in the corpus carry it.

    The .hdc writer round-tripped it and this exporter did not, so the SAME
    character kept its overrides through one export shape and lost them
    through the other. NOTES was worse than absent: ``_ATTR`` accepted it on
    input and nothing emitted it, which reads as support and behaves as a
    delete.
    """
    doc = {
        "powers": [{
            "id": 1,
            "xmlid": "ENERGYBLAST",
            "levels": 5,
            "text": "<i>Sunbolt:</i>  a wording HD would never generate",
            "notes": "remember to ask the GM about this one",
        }],
    }
    hero = build_from_json(doc)
    power = hero.powers[0]
    assert power.text_output == "<i>Sunbolt:</i>  a wording HD would never generate"
    assert power.notes == "remember to ask the GM about this one"

    out = to_build_json(hero)[ "powers"][0]
    assert out["text"] == doc["powers"][0]["text"], "the user's wording was dropped"
    assert out["notes"] == doc["powers"][0]["notes"], "the user's notes were dropped"

    # And again, so the second lap cannot quietly differ from the first.
    again = build_from_json(to_build_json(hero)).powers[0]
    assert again.text_output == power.text_output
    assert again.notes == power.notes
