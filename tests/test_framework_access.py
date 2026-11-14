"""Tests for kirby_cost.io.framework_access — read-only build-model accessors.

These tests confirm that downstream consumers (a downstream consumer) can reach
framework kind / reserve / slot-variable-flag / AVAD alternate-defense through
the accessor module without reaching into object internals.
"""
import pytest
from tests.corpus import require_authored_hdc
from tests.own_copy import own_copy
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.io.framework_access import (
    framework_kind,
    reserve_or_pool,
    slot_is_variable,
    avad_alternate_defense,
    framework_slots,
)

# The maintainer's own characters, bundled: PowerLad has an all-Ultra Multipower,
# Ravel a Variable Power Pool.
POWERLAD = str(require_authored_hdc("PowerLad"))
RAVEL = str(require_authored_hdc("Ravel"))


def _load():
    return HDCLoader().load_file(POWERLAD)


# PowerLad's Multipower (ID 1727271632187) gains one AVAD slot, on a temporary
# copy: none of the maintainer's characters has an alternate-defense attack.
_MP_ID = "1727271632187"
_AVAD_DEFENSE = "Life Support (Safe Environment: Intense Heat) Or Fire/Heat Powers"
_AVAD_SLOT = (
    f'<POWER XMLID="ENERGYBLAST" ID="9000000000040" BASECOST="0.0" LEVELS="6" '
    f'ALIAS="Energy Blast" POSITION="99" MULTIPLIER="1.0" PARENTID="{_MP_ID}" '
    f'ULTRA_SLOT="Yes" NAME="Withering Heat" QUANTITY="1" AFFECTS_PRIMARY="Yes" '
    f'AFFECTS_TOTAL="Yes" INPUT="ED">'
    f'<MODIFIER XMLID="AVAD" ID="9000000000041" BASECOST="1.0" LEVELS="0" ALIAS="Attack Versus Alternate Defense" '
    f'POSITION="-1" MULTIPLIER="1.0" OPTION="VERYUNCOMMON" OPTIONID="VERYUNCOMMON" '
    f'OPTION_ALIAS="Very Common -> Uncommon" INPUT="{_AVAD_DEFENSE}" PRIVATE="No" FORCEALLOW="No" />'
    f'</POWER>')


def _load_with_avad(tmp_path):
    return HDCLoader().load_file(
        own_copy(tmp_path, section_xml=[("POWERS", _AVAD_SLOT)]))


def test_powerlad_has_a_multipower():
    hero = _load()
    frameworks = [p for p in hero.powers if framework_kind(p) is not None]
    assert frameworks, "PowerLad should have at least one framework"
    kinds = {framework_kind(p) for p in frameworks}
    assert "multipower" in kinds


def test_multipower_reserve_is_positive():
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    assert reserve_or_pool(mp) > 0, "PowerLad MP should have a nonzero reserve"


def test_powerlad_mp_reserve_is_45():
    """PowerLad's Brick Tricks is a 45-point Multipower."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    assert reserve_or_pool(mp) == 45


def test_framework_slots_returns_only_direct_children():
    """framework_slots() must return only powers whose .parent is the framework."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    assert len(slots) > 0, "Multipower should have at least one slot"
    for s in slots:
        assert s.parent is mp, "Every returned slot must reference the framework as parent"


def test_avad_alternate_defense_found(tmp_path):
    """The AVAD 'Withering Heat' slot should expose a non-empty alternate defense string."""
    hero = _load_with_avad(tmp_path)
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    avad_defenses = [avad_alternate_defense(s) for s in slots]
    assert any(avad_defenses), "At least one slot should have an AVAD/NND modifier"


def test_avad_alternate_defense_content(tmp_path):
    """The AVAD defense string for Withering Heat should mention 'Life Support' or 'Fire'."""
    hero = _load_with_avad(tmp_path)
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
    # The Big Wrap-Up has no AVAD modifier
    lb = next((p for p in hero.powers if getattr(p, "name", None) == "The Big Wrap-Up"), None)
    assert lb is not None, "PowerLad should have a 'The Big Wrap-Up' power"
    assert avad_alternate_defense(lb) is None


def test_slot_is_variable_flag_is_bool():
    """slot_is_variable must return a bool for every slot in the Multipower."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    for s in slots:
        result = slot_is_variable(mp, s)
        assert isinstance(result, bool), f"slot_is_variable must return bool, got {type(result)} for {s.name!r}"


def test_powerlad_all_slots_are_ultra():
    """All PowerLad slots are Ultra (u), so slot_is_variable should be False for all."""
    hero = _load()
    mp = next(p for p in hero.powers if framework_kind(p) == "multipower")
    slots = framework_slots(hero, mp)
    for s in slots:
        assert not slot_is_variable(mp, s), f"Slot {getattr(s,'name',None)!r} is ultra but slot_is_variable returned True"


def test_ravel_vpp_pool_is_levels_not_basecost():
    from kirby_cost.io.framework_access import framework_kind, vpp_pool, vpp_control
    hero = HDCLoader().load_file(RAVEL)
    vpp = next(p for p in hero.powers if framework_kind(p) == "vpp")
    assert vpp_pool(vpp) == 20        # pool = levels, NOT base_cost (0 for a VPP)
    ctl = vpp_control(vpp)
    # Ravel's pool is changed on a Skill Roll (no input names the skill) and
    # carries no Extra Time.
    assert ctl == {"skill_xmlid": None}


def test_framework_kind_non_framework_returns_none():
    """Powers that are not frameworks should return None from framework_kind."""
    hero = _load()
    # Find a plain power (not a framework)
    plain = next(
        p for p in hero.powers if framework_kind(p) is None
    )
    assert framework_kind(plain) is None
