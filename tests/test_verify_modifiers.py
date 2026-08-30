"""verify_modifiers() is GenericObject.verifyModifiers() (GenericObject.java:4338-4630)
without the dialogs: the same walk, returning what HD would have complained about.
The stateful fixture's `assigned` and `framework` rows are the oracle: an object
whose rows all agree must verify clean; an object with a refused row must name it.

Two documented seams sit between this walk and those rows, and both are held
open by name rather than papered over:

* **Cells the engine already gets wrong.** ``included_stateful_known_gaps.json``
  is the shrink-only ledger of every stateful cell where the engine's
  ``included()`` disagrees with HD. ``verify_modifiers`` asks the engine, so on
  those cells it necessarily inherits the engine's answer. They are owned by
  ``tests/test_included_stateful.py`` -- excluded from BOTH sides here, never
  silently absorbed.
* **The oracle's tier-2 simplification.** The Java REMOVES a modifier from the
  object before re-asking it (GenericObject.java:4572); the oracle
  (CostCalculatorCLI.java, tier 2) asked with it still attached, on the
  reasoning that ``Modifier.included()`` does not read the object's own
  assigned list. That reasoning is wrong for three cells, because the engine
  derives duration/range/target FROM the assigned modifiers -- so removing the
  modifier changes the answer. This port follows the JAVA; the three cells are
  named in ``ORACLE_TIER2_SIMPLIFICATION`` below.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest

from tests.matrix_support import (hdc_id, object_index, sink_hero, stateful_cells,
                                  stateful_key)

LEDGER_PATH = Path(__file__).parent / "fixtures" / "included_stateful_known_gaps.json"

# (object id, modifier xmlid) cells where this walk and the oracle's `assigned`
# rows differ ONLY because the Java removes the modifier before re-asking and
# the oracle did not. Verified one at a time: with the modifier still attached
# the engine returns HD's own verdict (these cells are NOT in the gap ledger);
# detached, the derived state the modifier itself creates goes away.
ORACLE_TIER2_SIMPLIFICATION = {
    # PERSISTENT is what makes this Resistant Protection Persistent; detached,
    # "Resistant Protection is already Persistent." no longer applies.
    ("20260830000017", "PERSISTENT"): "hd_only",
    # NORANGE is what makes this Blast unranged; detached it is a Ranged Power
    # again, which is exactly what "No Range can only be applied to Ranged
    # Powers." asks for.
    ("20260830000022", "NORANGE"): "hd_only",
    # The mirror case: AOE is what re-targets this (self-only) Resistant
    # Protection onto a hex. Detached, the slot is self-targeted and AOE is
    # refused -- HD's walk sees the refusal, the oracle's ask did not.
    ("20260830000057", "AOE"): "py_only",
}


def _ledger() -> dict[str, str]:
    if not LEDGER_PATH.exists():
        return {}
    return json.loads(LEDGER_PATH.read_text()).get("gaps", {})


def _hd_refusals() -> tuple[dict, dict]:
    """(expected refusals, cells to ignore) per object, from the fixture.

    An ``assigned`` row belongs to its own object with slot ``None``; a
    ``framework`` row belongs to the framework LIST (``parent_id``, which a
    compound constituent's row carries too) with the slot named.
    """
    expected = collections.defaultdict(set)
    ignored = collections.defaultdict(set)
    ledger = _ledger()
    for c in stateful_cells():
        if c["tier"] == "template":
            continue
        owner = c["object_id"] if c["tier"] == "assigned" else c["parent_id"]
        cell = (c["modifier"], None if c["tier"] == "assigned" else c["object_id"])
        if stateful_key(c) in ledger:
            ignored[owner].add(cell)          # a known engine gap; not this test's verdict
            continue
        simplification = ORACLE_TIER2_SIMPLIFICATION.get((c["object_id"], c["modifier"]))
        if c["tier"] == "assigned" and simplification == "hd_only":
            continue                          # HD's walk detaches it; the refusal evaporates
        if c["tier"] == "assigned" and simplification == "py_only":
            expected[owner].add(cell)         # HD's walk detaches it; the refusal appears
            continue
        if not c["allowed"]:
            expected[owner].add(cell)
    return expected, ignored


def test_verify_matches_hd_on_every_sink_object():
    index = object_index(sink_hero())
    expected, ignored = _hd_refusals()
    for oid, obj in index.items():
        got = {(m.xmlid, (hdc_id(slot) if slot is not None else None))
               for m, slot, _ in obj.verify_modifiers()}
        assert got - ignored.get(oid, set()) == expected.get(oid, set()), \
            f"{obj.display} ({oid}): verify_modifiers disagrees with HD"


def test_the_framework_walk_names_a_slot_and_a_reason():
    """The List branch is the half the plain-object loop cannot reach: every
    refusal it returns must name the slot it is about, with HD's words."""
    index = object_index(sink_hero())
    mp = next(o for o in sink_hero().powers if o.name == "Multipower")
    findings = mp.verify_modifiers()
    assert findings, "the sink's Multipower is built to carry refused common modifiers"
    for mod, slot, reason in findings:
        assert slot is not None and hdc_id(slot) in index
        assert reason.strip()


def test_verify_never_mutates():
    hero = sink_hero()
    mp = next(o for o in hero.powers if o.name == "Multipower")
    before = [(m.xmlid, id(m)) for m in mp.assigned_modifiers]
    slots_before = [[m.xmlid for m in s.assigned_modifiers] for s in mp.objects]
    parents_before = [s.parent for s in mp.objects]
    mp.verify_modifiers()
    assert [(m.xmlid, id(m)) for m in mp.assigned_modifiers] == before
    assert [[m.xmlid for m in s.assigned_modifiers] for s in mp.objects] == slots_before
    assert [s.parent for s in mp.objects] == parents_before


def test_verify_restores_everything_when_an_included_raises():
    """The restoration is in ``finally``: a modifier whose ``included()``
    blows up must still leave the framework exactly as it was."""
    hero = sink_hero()
    mp = next(o for o in hero.powers if o.name == "Multipower")
    slot = mp.objects[0]
    slot_list_before = slot.assigned_modifiers
    slot_mods_before = list(slot_list_before)
    parent_before, check_before = slot.parent, slot.list_mod_check
    mods_before = list(mp.assigned_modifiers)

    victim = mp.assigned_modifiers[0]

    def boom(_obj):
        raise RuntimeError("included() exploded")

    original = victim.included
    victim.included = boom
    try:
        with pytest.raises(RuntimeError):
            mp.verify_modifiers()
    finally:
        victim.included = original

    assert slot.assigned_modifiers is slot_list_before
    assert list(slot.assigned_modifiers) == slot_mods_before
    assert slot.parent is parent_before
    assert slot.list_mod_check == check_before
    assert list(mp.assigned_modifiers) == mods_before
