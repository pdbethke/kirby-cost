"""Round-trip fidelity for explicit BASECOST="0.0" in HDC.

Bug: build_json.py emitted base_cost only when truthy, so an explicit
BASECOST="0.0" was dropped from the build doc.  On rebuild the loader saw
no BASECOST and applied the template default (which can be nonzero).
Canonical instance: a CV2 villain's TRIGGER modifier → RESET adder with
BASECOST="0.0" OPTIONID=HALFPHASE; template default for RESET resolves to
TURN (-0.5). Round-trip drift on that character: the power's real_cost 22 → 19,
total_points 574.0 → 571.0. The tests below use a temporary copy of PowerLad
with a Teleportation carrying the same Trigger/Reset shape.

Fix (fix(build-doc) commit): emit base_cost when `value or _base_cost_from_xml`
— provenance flag rather than truthiness.
"""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.io import to_build_json, build_from_json
from tests.own_copy import powerlad_with_triggered_teleport


@pytest.fixture
def loaded(tmp_path):
    return HDCLoader().load_file(powerlad_with_triggered_teleport(tmp_path))


def _find_teleport_with_trigger(hero):
    """Return the TELEPORTATION power that has a TRIGGER modifier ."""
    return next(
        (p for p in hero.powers
         if p.xmlid == "TELEPORTATION"
         and any(m.xmlid == "TRIGGER" for m in getattr(p, "_assigned_modifiers", []))),
        None,
    )


def test_explicit_zero_basecost_survives_round_trip(loaded):
    """TRIGGER's RESET adder carries explicit BASECOST="0.0" (HALFPHASE option);
    the template default for RESET is nonzero (TURN = -0.5).  Truthiness-dropping
    the explicit zero made rebuilds fall back to the default: 22 -> 19.
    """
    doc = to_build_json(loaded)
    rebuilt = build_from_json(doc)

    tele = _find_teleport_with_trigger(loaded)
    assert tele is not None, "Source TELEPORTATION+TRIGGER power not found in loaded"
    tele_back = _find_teleport_with_trigger(rebuilt)
    assert tele_back is not None, "TELEPORTATION+TRIGGER power not found in rebuilt"

    assert tele_back.real_cost_pre_list == tele.real_cost_pre_list == 12.0


def test_total_points_survive_round_trip(loaded):
    """total_points must be identical after build-doc round-trip.

    Previously a gap existed (3 points on the CV2 villain) caused by the
    explicit BASECOST=0.0 drop on the TRIGGER/RESET adder.
    """
    rebuilt = build_from_json(to_build_json(loaded))
    assert rebuilt.total_points == loaded.total_points == 411.5


def test_zero_basecost_in_build_doc(loaded):
    """The build doc itself must carry base_cost=0.0 for the RESET adder.

    The doc emits alias not display, so we locate the TELEPORTATION power by
    finding the one that carries a TRIGGER modifier with a RESET adder.
    """
    doc = to_build_json(loaded)
    # Find the TELEPORTATION power that has a TRIGGER modifier 
    tele_doc = next(
        (o for o in doc["powers"]
         if o.get("xmlid") == "TELEPORTATION"
         and any(m["xmlid"] == "TRIGGER" for m in o.get("modifiers", []))),
        None,
    )
    assert tele_doc is not None, "Could not find TELEPORTATION+TRIGGER power in doc"

    # Find TRIGGER modifier
    trigger = next(
        (m for m in tele_doc.get("modifiers", []) if m["xmlid"] == "TRIGGER"),
        None,
    )
    assert trigger is not None, "TRIGGER modifier not found in doc"

    # Find RESET adder on the TRIGGER modifier
    reset = next(
        (a for a in trigger.get("adders", []) if a["xmlid"] == "RESET"),
        None,
    )
    assert reset is not None, "RESET adder not found on TRIGGER in doc"
    assert "base_cost" in reset, "base_cost=0.0 was dropped (truthiness bug)"
    assert reset["base_cost"] == 0.0
