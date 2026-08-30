"""Every included() question HD asks of the validation sink, against the engine.

Three tiers, one row shape (spec §3): ``template`` (every template modifier x
this loaded object), ``assigned`` (each modifier already on it, re-asked --
verifyModifiers' plain-object loop) and ``framework`` (each framework-common
modifier x each slot -- verifyModifiers' List walk). The sink is loaded through
HDCLoader, so this is the first matrix that measures the LOADER: a cell whose
echo shows HD's duration/cost differing from the loaded object's is the filed
loader follow-up, and is ledgered against it by name.

``included_stateful_known_gaps.json`` is SHRINK-ONLY, written only by
tests/included_ledger.py --stateful.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.matrix_support import (allows_other_modifiers, object_index, sink_hero,
                                  stateful_cells, stateful_key, template_modifier)

LEDGER_PATH = Path(__file__).parent / "fixtures" / "included_stateful_known_gaps.json"


def _ledger() -> dict[str, str]:
    if not LEDGER_PATH.exists():
        return {}
    return json.loads(LEDGER_PATH.read_text()).get("gaps", {})


def _ask(cell: dict, index: dict) -> tuple[bool, str]:
    obj = index[cell["object_id"]]
    if cell["tier"] == "template":
        mod = template_modifier(cell["modifier"])
    elif cell["tier"] == "assigned":
        mod = next(m for m in obj.assigned_modifiers if m.xmlid == cell["modifier"])
    else:  # framework: the common modifier asked of the slot, slot detached, as the Java does
        # A via_compound row's slot is a Compound Power constituent: its
        # own .parent is never set at load time (only .main_power is --
        # CompoundPower's cost methods reparent transiently and restore
        # None), so the framework common modifiers live on the COMPOUND's
        # parent, not the constituent's. Java detaches both the constituent
        # and its compound from the List before asking.
        compound_id = cell.get("via_compound")
        if compound_id:
            compound = index[compound_id]
            parent = compound.parent
            mod = next(m for m in parent.assigned_modifiers if m.xmlid == cell["modifier"])
            orig_obj_parent = obj.parent
            obj.parent = None
            compound.parent = None
            obj.list_mod_check = True
            try:
                if not allows_other_modifiers(obj):
                    return False, f"{obj.alias} does not allow modifiers with its current configuration."
                reason = mod.included(obj) or ""
            finally:
                obj.list_mod_check = False
                obj.parent = orig_obj_parent
                compound.parent = parent
            return reason.strip() == "", reason
        parent = obj.parent
        mod = next(m for m in parent.assigned_modifiers if m.xmlid == cell["modifier"])
        obj.parent = None
        obj.list_mod_check = True
        try:
            if not allows_other_modifiers(obj):
                return False, f"{obj.alias} does not allow modifiers with its current configuration."
            reason = mod.included(obj) or ""
        finally:
            obj.list_mod_check = False
            obj.parent = parent
        return reason.strip() == "", reason
    reason = mod.included(obj) or ""
    return reason.strip() == "", reason


def _survey() -> dict[str, str]:
    """{cell key: what went wrong} for every cell the engine disagrees on."""
    hero = sink_hero()
    index = object_index(hero)
    wrong: dict[str, str] = {}
    for c in stateful_cells():
        key = stateful_key(c)
        try:
            allowed, reason = _ask(c, index)
        except FileNotFoundError:
            raise  # no template configured -> conftest turns it into a skip
        except Exception as e:  # noqa: BLE001 -- a crash is a gap too
            wrong[key] = f"raised {type(e).__name__}: {e}"
            continue
        if allowed != c["allowed"] or reason != c["reason"]:
            wrong[key] = (f"engine allowed={allowed} {reason!r}  HD allowed={c['allowed']} {c['reason']!r}"
                          f"  HD state={json.dumps(c['state'], sort_keys=True)}")
    return wrong


@pytest.fixture(scope="module")
def survey():
    return _survey()


def test_the_stateful_matrix_is_substantial():
    tiers = {c["tier"] for c in stateful_cells()}
    assert tiers == {"template", "assigned", "framework"}
    assert len(stateful_cells()) > 3000


def test_every_fixture_object_loads():
    """A row whose object the loader did not produce is a loader gap, named."""
    index = object_index(sink_hero())
    missing = sorted({c["object_id"] for c in stateful_cells()} - set(index))
    assert not missing, f"objects HD saw that HDCLoader did not load: {missing}"


def test_no_new_disagreement_with_hero_designer(survey):
    new = {k: v for k, v in survey.items() if k not in _ledger()}
    if new:
        lines = [f"{len(new)} stateful cells disagree with HD and are not in the ledger "
                 f"({len(stateful_cells()) - len(survey):,}/{len(stateful_cells()):,} exact):"]
        for k, v in sorted(new.items())[:25]:
            lines.append(f"  {k}\n      {v}")
        pytest.fail("\n".join(lines))


def test_the_ledger_is_not_stale(survey):
    fixed = sorted(set(_ledger()) - set(survey))
    if fixed:
        pytest.fail(f"{len(fixed)} ledger entries now agree with HD. Remove them from "
                    f"{LEDGER_PATH.name} in the commit that fixed them:\n  " + "\n  ".join(fixed))
