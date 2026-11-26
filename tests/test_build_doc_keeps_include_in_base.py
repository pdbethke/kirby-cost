"""A build doc keeps an adder's INCLUDEINBASE, so a rebuilt power keeps its range.

A 6E power's range is ten metres per point of total cost with every adder
NOT in the base subtracted first (`GenericObject.range_value`, after HD's
getRangeValue). The doc carried no INCLUDEINBASE, so a rebuilt adder read
False and its cost came off the range: Bokor's Digitalis dust (a 5-point
Multipower slot whose +1 pip is in the base) reached 50m from his .hdc and
0m from his build doc. Found 2026-11-26 by the workshop DC limit, which read
the rebuilt range to tell a ranged attack from a HTH one.
"""
from __future__ import annotations

from kirby_cost.io.build_json import build_from_json, to_build_json
from kirby_cost.io.formats import load_build
from tests.corpus import require_authored_hdc


def _by_id(hero):
    return {str(p.id): p for p in hero.powers}


def test_a_rebuilt_power_keeps_its_range():
    original = load_build(str(require_authored_hdc("Bokor")), format="hdc")
    before = {k: p.range_value for k, p in _by_id(original).items()}
    rebuilt = build_from_json(to_build_json(original))
    after = {k: p.range_value for k, p in _by_id(rebuilt).items()}
    assert after == before


def test_every_authored_adders_include_in_base_survives():
    for name in ("Ravel", "Bokor", "PowerLad"):
        original = load_build(str(require_authored_hdc(name)), format="hdc")
        # Adders get new ids on a rebuild; the owning power's id does not.
        flags = lambda h: sorted((str(p.id), a.xmlid, a.include_in_base())
                                 for p in h.powers for a in p.assigned_adders)
        assert flags(build_from_json(to_build_json(original))) == flags(original), name
