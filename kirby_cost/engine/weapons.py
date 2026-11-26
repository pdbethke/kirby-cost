"""Weapons, and whether a Weapon Element lets a style's maneuvers use one.

* A style's Martial Maneuvers work with a weapon only through a Weapon Element
  bought for that weapon's class, or when the style is weapon-based like
  Fencing (6E2 94). HD marks a weapon-based maneuver ``USEWEAPON``.
* A bought HKA is not a "weapon" by that page: 6E2 102 adds a Combat or
  Martial Maneuver to an HKA directly, with no Element. What 6E2 94 calls a
  weapon is a thing held, and 6E1 378-379 gives weapons as the usual Obvious,
  Accessible Focus. So here a weapon is a purchase in Equipment, or one with a
  Focus (its own or its framework's).
* HD records an Element's classes (adders: BLADES, AXESMACES, ...) but not the
  class of a weapon bought as a power -- an HKA named "Sword". The class is
  matched by the words of the class's name in the weapon's names; when they
  do not meet, the answer is UNKNOWN (workshop plan 1b, R14), never a guess.
"""
from __future__ import annotations

from kirby_cost.engine.csl import Reach

#: Element adders that name no class of weapon: the bare hand, and the
#: style's own default (which the style, not the build, defines).
_NOT_A_CLASS = frozenset({"BAREHAND"})
_UNSTATED = frozenset({"DEFAULTELEMENT"})
#: Words in a class's name that say nothing about which weapon it is.
_FILLER = frozenset({"and", "the", "common", "uncommon", "melee", "weapon",
                     "weapons", "other"})


def _modifiers(obj) -> list:
    mods = list(getattr(obj, "assigned_modifiers", None) or [])
    parent = getattr(obj, "parent", None)
    if parent is not None:
        mods += list(getattr(parent, "assigned_modifiers", None) or [])
    return mods


def is_weapon(obj, *, section: str) -> bool:
    """A purchase in Equipment, or one with a Focus (6E2 94; 6E1 378-379)."""
    if section == "equipment":
        return True
    return any((getattr(m, "xmlid", "") or "").upper() == "FOCUS"
               for m in _modifiers(obj))


def _words(text: str) -> set[str]:
    out = set()
    for raw in "".join(c if c.isalnum() else " " for c in text.lower()).split():
        if raw in _FILLER or len(raw) < 3:
            continue
        out.add(raw[:-1] if raw.endswith("s") and len(raw) > 3 else raw)
    return out


def element_classes(hero) -> list:
    """Every Weapon Element class adder the build carries."""
    found = []
    for obj in getattr(hero, "maneuvers", None) or []:
        if (getattr(obj, "xmlid", "") or "").upper() == "WEAPON_ELEMENT":
            found.extend(getattr(obj, "assigned_adders", None) or [])
    return found


def element_reach(hero, labels) -> Reach:
    """Whether the build's Weapon Elements cover a weapon going by
    ``labels`` (its name, its framework's). NO when the build has no
    Element at all; YES when a class's words appear in a label; UNKNOWN
    when it has Elements but none can be told to fit."""
    classes = [a for a in element_classes(hero)
               if (getattr(a, "xmlid", "") or "").upper() not in _NOT_A_CLASS]
    if not classes:
        return Reach.NO
    names = set()
    for label in labels:
        names |= _words(label or "")
    for adder in classes:
        if (getattr(adder, "xmlid", "") or "").upper() in _UNSTATED:
            continue
        display = getattr(adder, "display", None) or getattr(adder, "alias", "") or ""
        if _words(display) & names:
            return Reach.YES
    return Reach.UNKNOWN


__all__ = ["element_classes", "element_reach", "is_weapon"]
