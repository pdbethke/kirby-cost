"""A Vehicle6E character's PD/ED cost the template's rate, not Main6E's.

`Vehicle6E.hdt` prices PD and ED at `LVLCOST=3, LVLVAL=2` — 1.5 CP per point —
where `Main6E.hdt` uses `1, 1`. WARLORD - THE FLYING FORTRESS buys 10 of each,
so the template rate is 15 and the Main6E rate is 10.

**This file previously asserted the exact opposite**, and the reasoning is worth
keeping because it was careful and still wrong.

It said Hero Designer ignores the template here, and backed it with a
measurement across all 655 fixtures: the oracle recorded PD at
`(level_cost, level_value) = (1.0, 1.0)` for every character on every template
— Automaton6E 16, Heroic6E 238, Superheroic6E 300, Vehicle6E 4, no-template 11
— with not one instance at `(3, 2)`. On that basis the loader's
`_apply_vehicle6e_overrides` was gutted for diverging from the oracle.

The measurement was real and the conclusion was wrong, because the oracle was
wrong. The headless HD fork could not resolve any `builtIn.` template name, so
it costed every character against its Main6E bootstrap no matter what the file
declared — which is precisely why PD looked like `(1, 1)` everywhere, including
on the four Vehicle6E characters. Fixed 2026-08-17; the oracle now says
`(3.0, 2.0)` for this character, and the engine agrees because it resolves the
declared template.

The assertion below compares engine to oracle rather than to a literal, which
is why it survived the reversal unchanged. That is the useful shape: assert the
relationship, not the number you expect today.
"""
import json
import glob

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

FIXTURE = glob.glob("tests/fixtures/oracle/*WARLORD*FLYING*.json")


@pytest.mark.skipif(not FIXTURE, reason="WARLORD oracle fixture not present")
def test_vehicle6e_pd_matches_the_oracle():
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
            f"({o['level_cost']}, {o['level_value']}). A character is costed "
            "against the template it declares, and Vehicle6E prices PD/ED at 3 per 2."
        )
        assert c.total_cost == o["total_cost"], (
            f"{c.xmlid}: engine {c.total_cost} vs oracle {o['total_cost']}"
        )
