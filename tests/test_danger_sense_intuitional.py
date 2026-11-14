"""INTUITIONAL survives when AREA/SENSITIVITY carry their qualifying options.

Root cause of a corpus oracle failure (a villain's DANGER_SENSE py=36.0 vs oracle=31.0,
exactly the -5 INTUITIONAL adder being dropped).
The test below builds the same Talent on a temporary copy of PowerLad.

com/hero/objects/talents/DangerSense.java getAssignedAdders():

    if (intuitional == null) return ret;
    else if (((where == null) || where.getSelectedOption().getXMLID()
                 .equals("IMMEDIATE_VICINITY"))
          && ((which == null) || which.getSelectedOption().getXMLID()
                 .equals("OUT_OF_COMBAT")))
        return ret;                      // KEEP intuitional
    else { ret.remove(intuitional); }    // DROP it

That character had AREA=IMMEDIATE_VICINITY and SENSITIVITY=OUT_OF_COMBAT, so Java
keeps the -5: 15 base + 9 levels + (5 + 5 + 2 - 5) = 31.

The Python port mirrored that structure faithfully but could never satisfy it:
the loader read each ADDER's OPTIONID, passed it to the template, and then threw
it away instead of storing it on the adder. Every adder had option_id None, so
both option checks were False and the -5 was always dropped. The POWER branch
persists OPTIONID (`if option_id: obj.option_id = option_id`); the ADDER
branches did not.
"""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.own_copy import own_copy


def _adder(xmlid, adder_id, base, option=None):
    opt = f' OPTION="{option}" OPTIONID="{option}"' if option else ""
    return (f'<ADDER XMLID="{xmlid}" ID="{adder_id}" BASECOST="{base}" LEVELS="0" '
            f'ALIAS="{xmlid}" POSITION="-1" MULTIPLIER="1.0"{opt} SHOWALIAS="Yes" '
            f'PRIVATE="No" REQUIRED="No" INCLUDEINBASE="No" DISPLAYINSTRING="Yes" '
            f'GROUP="No" SELECTED="YES" />')


_DANGER_SENSE = (
    '<DANGER_SENSE XMLID="DANGER_SENSE" ID="9000000000100" BASECOST="15.0" LEVELS="9" '
    'ALIAS="Danger Sense" POSITION="0" MULTIPLIER="1.0">'
    + _adder("AREA", 9000000000101, 5.0, "IMMEDIATE_VICINITY")
    + _adder("SENSITIVITY", 9000000000102, 5.0, "OUT_OF_COMBAT")
    + _adder("SENSE", 9000000000103, 2.0)
    + _adder("INTUITIONAL", 9000000000104, -5.0)
    + "</DANGER_SENSE>")


def test_adder_optionid_is_persisted_and_intuitional_is_kept(tmp_path):
    hero = HDCLoader().load_file(
        own_copy(tmp_path, section_xml=[("TALENTS", _DANGER_SENSE)]))
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

    assert ds.total_cost == 31.0, (
        f"DANGER_SENSE cost {ds.total_cost}, expected 31.0 "
        "(15 base + 9 levels + 5 + 5 + 2 - 5)"
    )
