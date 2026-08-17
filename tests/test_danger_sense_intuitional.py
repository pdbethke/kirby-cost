"""INTUITIONAL survives when AREA/SENSITIVITY carry their qualifying options.

Root cause of the BOREALIS oracle failure (DANGER_SENSE py=36.0 vs oracle=31.0,
exactly the -5 INTUITIONAL adder being dropped).

com/hero/objects/talents/DangerSense.java getAssignedAdders():

    if (intuitional == null) return ret;
    else if (((where == null) || where.getSelectedOption().getXMLID()
                 .equals("IMMEDIATE_VICINITY"))
          && ((which == null) || which.getSelectedOption().getXMLID()
                 .equals("OUT_OF_COMBAT")))
        return ret;                      // KEEP intuitional
    else { ret.remove(intuitional); }    // DROP it

Borealis has AREA=IMMEDIATE_VICINITY and SENSITIVITY=OUT_OF_COMBAT, so Java
keeps the -5: 15 base + 9 levels + (5 + 5 + 2 - 5) = 31.

The Python port mirrored that structure faithfully but could never satisfy it:
the loader read each ADDER's OPTIONID, passed it to the template, and then threw
it away instead of storing it on the adder. Every adder had option_id None, so
both option checks were False and the -5 was always dropped. The POWER branch
persists OPTIONID (`if option_id: obj.option_id = option_id`); the ADDER
branches did not.
"""
import glob
import json
import pathlib

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

FIXTURE = glob.glob("tests/fixtures/oracle/*BOREALIS*.json")


@pytest.mark.skipif(not FIXTURE, reason="BOREALIS oracle fixture not present")
def test_adder_optionid_is_persisted_and_intuitional_is_kept():
    fx = json.load(open(FIXTURE[0]))
    if not pathlib.Path(fx["hdc_path"]).exists():
        pytest.skip("HDC source not present on this machine")

    hero = HDCLoader().load_file(fx["hdc_path"])
    ds = next((t for t in hero.talents if t.xmlid == "DANGER_SENSE"), None)
    assert ds is not None, "DANGER_SENSE not loaded"

    opts = {a.xmlid: getattr(a, "option_id", None) for a in ds._assigned_adders}
    assert opts.get("AREA") == "IMMEDIATE_VICINITY", (
        f"AREA option_id is {opts.get('AREA')!r}; the loader must persist an "
        "ADDER's OPTIONID onto the adder, as the POWER branch already does."
    )
    assert opts.get("SENSITIVITY") == "OUT_OF_COMBAT", (
        f"SENSITIVITY option_id is {opts.get('SENSITIVITY')!r}"
    )

    kept = [a.xmlid for a in ds.assigned_adders]
    assert "INTUITIONAL" in kept, (
        "INTUITIONAL was dropped. DangerSense.java keeps it when AREA is "
        "IMMEDIATE_VICINITY and SENSITIVITY is OUT_OF_COMBAT."
    )

    oracle = next(t for t in fx["talents"] if t["xmlid"] == "DANGER_SENSE")
    assert ds.total_cost == oracle["total_cost"] == 31.0, (
        f"DANGER_SENSE cost {ds.total_cost}, oracle {oracle['total_cost']} "
        "(15 base + 9 levels + 5 + 5 + 2 - 5)"
    )
