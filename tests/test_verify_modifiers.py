"""verify_modifiers() is GenericObject.verifyModifiers() (GenericObject.java:4338-4630)
without the dialogs: the same walk, returning what HD would have complained about.
The stateful fixture's `assigned` and `framework` rows are the oracle: an object
whose rows all agree must verify clean; an object with a refused row must name it.

One documented seam sits between this walk and those rows, and is held open
by name rather than papered over:

* **Cells the engine already gets wrong.** ``included_stateful_known_gaps.json``
  is the shrink-only ledger of every stateful cell where the engine's
  ``included()`` disagrees with HD. ``verify_modifiers`` asks the engine, so on
  those cells it necessarily inherits the engine's answer. They are owned by
  ``tests/test_included_stateful.py`` -- excluded from BOTH sides here, never
  silently absorbed.

The oracle's ``assigned`` tier used to ask each modifier's ``included()`` with
the modifier still attached, on the reasoning that ``Modifier.included()``
does not read the object's own assigned list. That reasoning was wrong for
three cells, because the engine derives duration/range/target FROM the
assigned modifiers -- so removing the modifier before asking (what the Java
actually does, ``GenericObject.java:4584-4661``) changes the answer.
``CostCalculatorCLI.java``'s ``assigned`` tier now mirrors the Java exactly
(remove, ask, restore, same list object) -- see kirby-hd-oracle
``feat/included-hdc``. Two of the three affected cells now agree without a
carve-out (they moved into the shrink-only ledger as ordinary regressions and
are excluded above like any other known engine gap).

The third -- ``PERSISTENT`` on object ``20260830000017`` ("Resistant
Protection") -- survives as its own named exception, ``LOADER_DIVERGENCE``,
below. It is NOT an oracle quirk: ``GenericObject.getDuration()``/
``getOrigDuration()`` (:1673-1765) read the object's raw ``duration`` FIELD
first, before any modifier presence check, so HD's refusal ("already
Persistent") holds whether or not PERSISTENT is attached -- removing it makes
no difference in the real Java, which is why the regenerated fixture's answer
for this cell did not move. Our port's ``duration``/``orig_duration``
properties read the same field (``base.py:824,994``), but this object's
loaded field is ``"CONSTANT"``, not HD's ``"PERSISTENT"`` -- the
constructor-hardcoded-duration loader follow-up (2026-08-30 anatomy note
Follow-ups (1)), filed and explicitly not to be fixed here. With the
modifier attached the loaded field is masked (the modifier-presence branch of
``duration`` returns ``"PERSISTENT"`` either way), so ``test_included_stateful``
sees no gap; only ``verify_modifiers``'s real removal exposes the field
underneath.

A second, unrelated exception, ``ID_COLLISION_DIVERGENCE``, holds two more
cells open for the pre-existing Multipower/VPP id-collision documented in
``task-4-report.md`` -- see it for the full account.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest

from tests.matrix_support import (hdc_id, object_index, sink_hero, stateful_cells,
                                  stateful_key)

LEDGER_PATH = Path(__file__).parent / "fixtures" / "included_stateful_known_gaps.json"

# (object id, modifier xmlid) cells where verify_modifiers' own detach-then-ask
# (correct: it mirrors GenericObject.java:4584-4661) disagrees with HD's real
# answer not because of an oracle simplification, but because the LOADED
# object's own state differs from HD's -- the loader follow-up, not a rule
# defect. See the module docstring for the one cell currently here.
LOADER_DIVERGENCE = {
    ("20260830000017", "PERSISTENT"): (
        "loader: orig_duration HD=PERSISTENT engine=CONSTANT; follow-up "
        "2026-08-30 anatomy note Follow-ups (1)"
    ),
}

# (object id, modifier xmlid) `assigned`-tier cells at a Multipower/VPP id HD's
# fixture carries as bare xmlid GENERIC_OBJECT (Task 4's "2 LINKED id-collision
# cells", ``task-4-report.md`` "Residual cells, corrected"). HD's fixture row
# asks the LIST itself and expects a flat (modifier, None) answer; the
# engine's ``object_index`` resolves this id to the real framework object
# (a Multipower here), whose ``verify_modifiers()`` correctly takes the List
# branch and returns one per-SLOT finding for each slot the modifier is
# refused on -- (modifier, slot_id) tuples, never (modifier, None). Same root
# cause as the two ledgered `template`-tier LINKED cells at this and the
# sibling VPP id; AOE/NND only started asserting it here once
# ``effective_target()`` (this round's item 2) made their answers agree with
# HD's, surfacing the shape mismatch this walk was already going to hit.
ID_COLLISION_DIVERGENCE = {
    ("20260830000043", "AOE"),
    ("20260830000043", "NND"),
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
        if c["tier"] == "assigned" and (c["object_id"], c["modifier"]) in LOADER_DIVERGENCE:
            ignored[owner].add(cell)          # loader follow-up, not a rule defect
            continue
        if c["tier"] == "assigned" and (c["object_id"], c["modifier"]) in ID_COLLISION_DIVERGENCE:
            ignored[owner].add(cell)          # harness id-collision, not a rule defect
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


def test_the_characteristic_clone_carries_the_heros_value():
    """GenericObject.java:4600-4614 -- a Characteristic that adds its
    modifiers to its base is not asked about itself: HD asks a CLONE whose
    levels include the hero's actual characteristic value, so a level-reading
    modifier sees the real total rather than the bought-up part alone.

    No fixture row reaches this branch (Task 1's oracle skipped it), so it is
    proved directly: the modifier's ``included`` records every object it is
    handed, and the last one -- the clone -- must carry own levels + the
    hero's value.
    """
    from kirby_cost.core.context import EngineContext
    from kirby_cost.io.hdc_loader import LoadedHero
    from kirby_cost.objects.characteristics.strength import Strength
    from kirby_cost.objects.modifier import Modifier

    hero_str = Strength()
    hero_str.xmlid = "STR"
    hero_str.levels = 15                      # characteristic_value() -> 15.0
    hero = LoadedHero()
    hero.characteristics = [hero_str]

    obj = Strength()
    obj.xmlid = "STR"
    obj.levels = 5
    obj.add_modifiers_to_base = True

    mod = Modifier()
    mod.xmlid = "TESTMOD"
    mod.alias = "Test"
    asked: list[tuple[bool, float]] = []
    mod.included = lambda o: asked.append((o is obj, o.levels)) or ""
    obj._assigned_modifiers.append(mod)

    previous = EngineContext.active_hero()
    EngineContext.set_active_hero(hero)
    try:
        assert obj.verify_modifiers() == []
    finally:
        EngineContext.set_active_hero(previous)

    assert asked == [(True, 5), (False, 20)], (
        "HD asks the object itself first (:4599), then a clone carrying the "
        "hero's value folded into levels (:4610)"
    )
