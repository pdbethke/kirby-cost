"""A power that runs off an Endurance Reserve says so in the build doc.

6E1 p.207: "A character with an Endurance Reserve must decide which powers
draw energy from the Reserve, and which draw energy from his personal END."
HD records that decision per power as USE_END_RESERVE="Yes". The loader read
it (`GenericObject.use_end_reserve`) and the .hdc writer wrote it back, but
the build doc --- `to_build_json` / `build_from_json`, the shape kirby-api
stores and kirby-combat fights from --- dropped it. Every power came back
drawing on personal END, so a reserve could never be spent from.

The fidelity gate (`test_build_doc_fidelity.py`) did not see it: it tests
the other JSON door, `hero.export(format="json")`, which is the .hdc's own
attributes as JSON and keeps them all.
"""
from kirby_cost.io.build_json import build_from_json, to_build_json

_DOC = {
    "name": "Battery", "template": "Main6E",
    "base_points": 400, "disad_points": 75, "experience": 0,
    "characteristics": [],
    "powers": [
        {"id": "R", "xmlid": "ENDURANCERESERVE", "levels": 40},
        {"id": "B", "xmlid": "ENERGYBLAST", "levels": 8, "input": "ED",
         "use_end_reserve": True},
        {"id": "F", "xmlid": "FLIGHT", "levels": 20},
    ],
    "skills": [], "perks": [], "talents": [], "disadvantages": [],
}


def _by_xmlid(hero):
    return {p.xmlid: p for p in hero.powers}


def test_the_doc_says_which_powers_draw_from_the_reserve():
    powers = _by_xmlid(build_from_json(_DOC))
    assert powers["ENERGYBLAST"].use_end_reserve is True
    assert powers["FLIGHT"].use_end_reserve is False


def test_and_says_it_back():
    doc = to_build_json(build_from_json(_DOC))
    flags = {p["xmlid"]: p.get("use_end_reserve") for p in doc["powers"]}
    assert flags["ENERGYBLAST"] is True
    assert flags["FLIGHT"] is None, "personal END is the absence, as HD writes it"
    again = _by_xmlid(build_from_json(doc))
    assert again["ENERGYBLAST"].use_end_reserve is True
