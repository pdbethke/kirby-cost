"""Tests for build_power_from_spec — the VPP on-the-fly power build+cost entry.

Cost ALWAYS comes from the engine; these tests assert against engine-computed
numbers and cross-check parity against the canonical HDC loader.
"""
from pathlib import Path

import pytest

from kirby_cost.services.power_builder import build_power_from_spec
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects.base import GenericObject

FIXTURES = Path(__file__).parent / "fixtures"


def test_builds_and_costs_a_blast():
    # 12 levels Energy Blast: confirm against the engine's own cost
    spec = {"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []}
    power, active, real = build_power_from_spec(spec)
    assert (getattr(power, "xmlid", "") or "").upper() == "ENERGYBLAST"
    assert active == 60      # engine-computed (5 pts/level * 12)
    assert real == 60        # no modifiers


def test_advantage_raises_active_cost():
    spec = {"xmlid": "ENERGYBLAST", "levels": 6,
            "modifiers": [{"xmlid": "AVAD", "base_cost": 1.0}]}
    power, active, real = build_power_from_spec(spec)
    assert active == 60      # 30 base active * (1 + 1.0 advantage) = 60


def test_unknown_xmlid_raises():
    with pytest.raises(ValueError):
        build_power_from_spec({"xmlid": "NOTAPOWER", "levels": 1})


@pytest.mark.skipif(
    not (FIXTURES / "ARTHON-CV1.hdc").exists(),
    reason="Hero Games character file not present (not shipped — see .gitignore)",
)
def test_matches_loader_cost_for_real_power():
    """Oracle cross-check: build a spec equivalent to a real loaded power and
    prove build_power_from_spec reproduces the loader's active_cost exactly."""
    loader = HDCLoader()
    hero = loader.load_file(str(FIXTURES / "ARTHON-CV1.hdc"))
    loader._ensure_registry_loaded()

    # Find a simple standalone attack power: registered xmlid, at least one
    # level, no assigned modifiers (so the equivalent spec is unambiguous).
    powers = list(getattr(hero, "powers", []) or [])
    candidate = None
    for p in powers:
        mods = getattr(p, "assigned_modifiers", None)
        if mods is None:
            mods = getattr(p, "_assigned_modifiers", [])
        xmlid = (p.xmlid or "").upper()
        if GenericObject._registry.get(xmlid) is None:
            continue
        if (getattr(p, "levels", 0) or 0) > 0 and not mods \
                and (getattr(p, "active_cost", 0) or 0) > 0:
            candidate = p
            break
    assert candidate is not None, "no simple costed power found in fixture"

    spec = {
        "xmlid": (candidate.xmlid or "").upper(),
        "levels": candidate.levels,
        "option_id": getattr(candidate, "option_id", None) or None,
        "modifiers": [],
    }
    _power, active, _real = build_power_from_spec(spec)
    assert active == int(round(candidate.active_cost)), (
        f"builder active {active} != loader active "
        f"{int(round(candidate.active_cost))} for {spec['xmlid']}"
    )
