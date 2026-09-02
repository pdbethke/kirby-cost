"""Finding a modifier on a purchase — once, for everyone who asks.

Three places needed the same question answered ("does this power carry
ARMORPIERCING / OIHID / RESISTANT, and at what level?") and three places
answered it differently:

  * ``GenericObject.find_object_by_id`` — the engine's own idiom, recursing
    through List ``objects`` and CompoundPower ``powers``. Used by ``duration``,
    ``uses_end``, ``does_body``.
  * ``kirby_cost.model.activation`` — that idiom plus the enclosing-purchase
    walk, because a slot is bound by its pool's limitations.
  * ``kirby_combat.hero_view._has_modifier`` / ``_modifier_levels`` — a flat
    ``for m in power.assigned_modifiers`` doing NEITHER, so a modifier on a
    power nested in a framework, or carried by the framework itself, was
    invisible to combat entirely.

The third is the one that bit: ARMORPIERCING, PENETRATING, HARDENED,
IMPENETRABLE and DOESBODY all read off that flat scan, so a slot of a
Multipower whose pool carries an Advantage fought without it.

Two rules, both inherited from the engine rather than invented here:

**Recursion** — a container holds its contents in ``objects`` (List) or
``powers`` (CompoundPower), so a scan that only reads ``assigned_modifiers``
stops at the first container.

**Inheritance** — an enclosing purchase's modifiers bind what it encloses. HD
prints a pool's limitations on each slot (``base.py``'s ``modifier_string``)
and Java's ``getAllAssignedModifiers`` merges an object's own modifiers with
its parent's (``base.py``'s ``_java_all_assigned_modifiers``). PRIVATE
modifiers are excluded: ``List.separatePrivateMods`` moves those off the
shared list precisely because they price the pool and do not reach its slots.
"""
from __future__ import annotations

from kirby_cost.objects.base import GenericObject


def enclosing_purchases(obj):
    """The purchases whose own modifiers also bind ``obj``, outermost last.

    Walks the whole chain rather than Java's single hop: a part of a Compound
    Power that is itself a Multipower slot sits two levels down — ``main_power``
    reaches the Compound Power, whose ``parent`` is the pool.
    """
    node = obj
    seen = {id(obj)}
    while True:
        nxt = getattr(node, "main_power", None)
        if nxt is None:
            nxt = getattr(node, "parent", None)
        if nxt is None or id(nxt) in seen:
            return
        seen.add(id(nxt))
        yield nxt
        node = nxt


def _find_own(obj, xmlid: str):
    return GenericObject.find_object_by_id(
        list(getattr(obj, "assigned_modifiers", None) or []), xmlid)


def find_modifier(obj, xmlid: str, *, inherited: bool = True):
    """The modifier ``xmlid`` binding ``obj``, or None.

    Set ``inherited=False`` to ask only what the purchase itself carries —
    which is the right question when the answer must not be attributed to the
    slot, and the wrong one for anything the rules apply to the slot in play.
    """
    own = _find_own(obj, xmlid)
    if own is not None or not inherited:
        return own
    for enclosing in enclosing_purchases(obj):
        shared = [m for m in (getattr(enclosing, "assigned_modifiers", None) or [])
                  if not getattr(m, "private", False)]
        found = GenericObject.find_object_by_id(shared, xmlid)
        if found is not None:
            return found
    return None


def has_modifier(obj, xmlid: str, *, inherited: bool = True) -> bool:
    return find_modifier(obj, xmlid, inherited=inherited) is not None


def modifier_levels(obj, xmlid: str, *, inherited: bool = True) -> int:
    """Levels on that modifier, 0 when it is absent (or carries none)."""
    found = find_modifier(obj, xmlid, inherited=inherited)
    return int(getattr(found, "levels", 0) or 0) if found is not None else 0
