"""Tests for kirby_cost.io.framework_access — read-only build-model accessors.

These tests confirm that downstream consumers (a downstream consumer) can reach
framework kind / reserve / slot-variable-flag / AVAD alternate-defense through
the accessor module without reaching into object internals.
"""
import pathlib

import pytest
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.io.framework_access import (
    framework_kind,
    reserve_or_pool,
    slot_is_variable,
    avad_alternate_defense,
    framework_slots,
)

# Champions Villains character files. Untracked since 2026-08-17: they are
# Hero Games content, and the repo ships none. Supply your own copies here, or
# these tests skip.
HELIOS = str(pathlib.Path(__file__).parent / "fixtures" / "HELIOS-CV1.hdc")
ARTHON = str(pathlib.Path(__file__).parent / "fixtures" / "ARTHON-CV1.hdc")

pytestmark = pytest.mark.skipif(
    not (pathlib.Path(HELIOS).exists() and pathlib.Path(ARTHON).exists()),
    reason="Hero Games character files not present (not shipped — see .gitignore)",
)


def _load():
    return HDCLoader().load_file(HELIOS)


def test_helios_has_a_multipower():
    hero = _load()
    frameworks = [p for p in hero.powers if framework_kind(p) is not None]
    assert frameworks, "Helios should have at least one framework"
    kinds = {framework_kind(p) for p in frameworks}
    assert "multipower" in kinds


def test_multipower_reserve_is_positive():
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    assert reserve_or_pool(mp) > 0, "Helios MP should have a nonzero reserve"


def test_helios_mp_reserve_is_75():
    """Helios Power Over Light And Heat is a 75-point Multipower."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    assert reserve_or_pool(mp) == 75


def test_framework_slots_returns_only_direct_children():
    """framework_slots() must return only powers whose .parent is the framework."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    assert len(slots) > 0, "Multipower should have at least one slot"
    for s in slots:
        assert s.parent is mp, "Every returned slot must reference the framework as parent"


def test_avad_alternate_defense_found():
    """The AVAD 'Withering Heat' slot should expose a non-empty alternate defense string."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    avad_defenses = [avad_alternate_defense(s) for s in slots]
    assert any(avad_defenses), "At least one slot should have an AVAD/NND modifier"


def test_avad_alternate_defense_content():
    """The AVAD defense string for Withering Heat should mention 'Life Support' or 'Fire'."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    avad_slots = [(s, avad_alternate_defense(s)) for s in slots if avad_alternate_defense(s)]
    assert avad_slots, "Expected at least one AVAD slot"
    _, defense = avad_slots[0]
    assert defense, "Defense string must be non-empty"
    assert "Life Support" in defense or "Fire" in defense or "Heat" in defense


def test_avad_alternate_defense_is_none_for_non_avad():
    """Powers without AVAD/NND should return None from avad_alternate_defense."""
    hero = _load()
    # Light Blast has no AVAD modifier
    lb = next((p for p in hero.powers if getattr(p, "name", None) == "Light Blast"), None)
    assert lb is not None, "Helios should have a 'Light Blast' power"
    assert avad_alternate_defense(lb) is None


def test_slot_is_variable_flag_is_bool():
    """slot_is_variable must return a bool for every slot in the Multipower."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    for s in slots:
        result = slot_is_variable(mp, s)
        assert isinstance(result, bool), f"slot_is_variable must return bool, got {type(result)} for {s.name!r}"


def test_helios_all_slots_are_ultra():
    """All Helios slots are Ultra (u), so slot_is_variable should be False for all."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    for s in slots:
        assert not slot_is_variable(mp, s), f"Slot {getattr(s,'name',None)!r} is ultra but slot_is_variable returned True"


def test_arthon_vpp_pool_is_levels_not_basecost():
    from kirby_cost.io.framework_access import framework_kind, vpp_pool, vpp_control
    hero = HDCLoader().load_file(ARTHON)
    vpp = next(p for p in hero.powers if framework_kind(p) == "vpp")
    assert vpp_pool(vpp) == 80        # pool = levels, NOT base_cost (0 for a VPP)
    ctl = vpp_control(vpp)
    assert ctl == {}                  # Arthon's VPP has no change-restriction modifier


def test_framework_kind_non_framework_returns_none():
    """Powers that are not frameworks should return None from framework_kind."""
    hero = _load()
    # Find a plain power (not a framework)
    plain = next(
        p for p in hero.powers if framework_kind(p) is None
    )
    assert framework_kind(plain) is None
