"""A Vehicle6E character's PD/ED cost the template's rate, not Main6E's.

`Vehicle6E.hdt` prices PD and ED at `LVLCOST=3, LVLVAL=2` — 1.5 CP per point —
where `Main6E.hdt` uses `1, 1`. A vehicle buying 10 of each pays 15 at the
template rate and 10 at the Main6E rate.

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
`(3.0, 2.0)` for a Vehicle6E character, and the engine agrees because it
resolves the declared template.

The assertion below states the template's own rate. It used to compare engine
to a per-character oracle fixture; none of the maintainer's own characters is
a vehicle, so it runs on a temporary Vehicle6E copy of PowerLad
(`tests.own_copy.vehicle_copy`), which no oracle dump covers.
"""
import os

import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.own_copy import vehicle_copy

pytestmark = pytest.mark.skipif(
    not os.environ.get("KIRBY_COST_HDT"), reason="no HERO Designer template configured")


def test_vehicle6e_pd_and_ed_use_the_template_rate(tmp_path):
    hero = HDCLoader().load_file(vehicle_copy(tmp_path))
    assert "Vehicle6E" in hero.template_name, "must be a Vehicle6E character"

    rated = {c.xmlid: c for c in hero.characteristics if c.xmlid in ("PD", "ED")}
    assert set(rated) == {"PD", "ED"}
    for xmlid, c in rated.items():
        assert (c._level_cost, c._level_value) == (3.0, 2.0), (
            f"{xmlid}: engine ({c._level_cost}, {c._level_value}). A character is "
            "costed against the template it declares, and Vehicle6E prices PD/ED "
            "at 3 per 2."
        )
