"""A Vehicle6E character's PD/ED cost the base rate, not the template's.

Root cause of the WARLORD - THE FLYING FORTRESS oracle failure (two
COMPOUNDPOWER mismatches, 42 vs 28 and 24 vs 16 -- each exactly 1.5x).

Vehicle6E.hdt and Base6E.hdt define PD/ED with LVLCOST=3, LVLVAL=2 (1.5 CP per
point) where Main6E.hdt uses LVLCOST=1, LVLVAL=1. The loader honoured that via
_apply_vehicle6e_overrides.

Hero Designer does not. Measured over all 655 oracle fixtures, the oracle's PD
(level_cost, level_value) is (1.0, 1.0) for EVERY character regardless of
template:

    Automaton6E 16    Heroic6E 238    Superheroic6E 300
    Vehicle6E    4    (no template) 11

Not one instance uses (3, 2). The engine's override therefore diverged from the
Java oracle, and parity with the oracle is the engine's contract.

The divergence was invisible on characteristics -- test_oracle_fixtures compares
powers/skills/perks/talents/martial_arts but NOT characteristics -- and only
surfaced where PD/ED were bought as sub-powers of a COMPOUNDPOWER.
"""
import json
import glob

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

FIXTURE = glob.glob("tests/fixtures/oracle/*WARLORD*FLYING*.json")


@pytest.mark.skipif(not FIXTURE, reason="WARLORD oracle fixture not present")
def test_vehicle6e_pd_costs_the_base_rate():
    fx = json.load(open(FIXTURE[0]))
    import pathlib
    if not pathlib.Path(fx["hdc_path"]).exists():
        pytest.skip("HDC source not present on this machine")

    hero = HDCLoader().load_file(fx["hdc_path"])
    assert "Vehicle6E" in hero.template_name, "fixture must be a Vehicle6E character"

    oracle = {o["xmlid"]: o for o in fx["characteristics"] if o["xmlid"] in ("PD", "ED")}
    for c in hero.characteristics:
        if c.xmlid not in oracle:
            continue
        o = oracle[c.xmlid]
        assert (c._level_cost, c._level_value) == (o["level_cost"], o["level_value"]), (
            f"{c.xmlid}: engine ({c._level_cost}, {c._level_value}) vs oracle "
            f"({o['level_cost']}, {o['level_value']}). Hero Designer uses the base "
            "rate for PD/ED on every template, including Vehicle6E."
        )
        assert c.total_cost == o["total_cost"], (
            f"{c.xmlid}: engine {c.total_cost} vs oracle {o['total_cost']}"
        )
