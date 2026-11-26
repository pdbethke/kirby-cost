"""The most velocity a character can bring to a Move Through.

Velocity adds damage to movement-based maneuvers (Move By v/10, Move Through
v/6, 6E2 58), in whole 6m / 10m only (6E2 101). How much a character can bring:

* A Move Through may be done at Noncombat speed, but not with
  Extra-Dimensional Movement, FTL Travel, Teleportation, any MegaScaled
  movement, or Telekinesis (6E2 72).
* Velocity builds across Phases (6E2 27), so the most he brings is his
  Noncombat velocity.
* Noncombat movement is double Combat movement for free; each +5 points
  doubles it again in one mode (6E1 157). HD records the extra doublings as the
  movement's ``IMPROVEDNONCOMBAT`` adder (LEVELS n is x2^(n+1)) and "no
  Noncombat movement" as the ``NONONCOMBAT`` modifier.
* Leaping differs (6E1 245): a Noncombat leap covers its multiple of the
  distance, but its duration in Phases equals the number of doublings. Its
  velocity per Phase is that distance over those Phases.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

#: Movement a Move Through may use (6E2 72 names what it may not).
_MOVES = frozenset({"RUNNING", "SWIMMING", "LEAPING", "FLIGHT", "TUNNELING",
                    "SWINGING", "GLIDING"})
#: Characteristic movement: its total is read off the sheet, powers included.
_CHARACTERISTIC_MOVES = frozenset({"RUNNING", "SWIMMING", "LEAPING"})


@dataclass(frozen=True)
class Velocity:
    """A velocity in meters per Phase, and the movement it comes from."""

    meters: float
    xmlid: str
    #: The purchase that carries it (HD ID), None for a characteristic.
    hd_id: str | None


def _modifiers(obj) -> list:
    mods = list(getattr(obj, "assigned_modifiers", None) or [])
    parent = getattr(obj, "parent", None)
    if parent is not None:
        mods += list(getattr(parent, "assigned_modifiers", None) or [])
    return mods


def _has_modifier(obj, xmlid: str) -> bool:
    return any((getattr(m, "xmlid", "") or "").upper() == xmlid
               for m in _modifiers(obj))


def noncombat_multiplier(obj) -> int:
    """x2 free, doubled per IMPROVEDNONCOMBAT level, x1 with NONONCOMBAT
    (6E1 157)."""
    if _has_modifier(obj, "NONONCOMBAT"):
        return 1
    for adder in getattr(obj, "assigned_adders", None) or []:
        if (getattr(adder, "xmlid", "") or "").upper() == "IMPROVEDNONCOMBAT":
            return 2 ** (int(adder.levels) + 1)
    return 2


def phase_velocity(xmlid: str, combat_meters: float, multiplier: int) -> float:
    """Meters per Phase at Noncombat speed. For Leaping, the distance over
    the Phases the leap lasts (6E1 245)."""
    if xmlid == "LEAPING" and multiplier > 1:
        doublings = int(math.log2(multiplier))
        return combat_meters * multiplier / doublings
    return combat_meters * multiplier


def best_move_through_velocity(hero, *, in_hero_id: bool) -> Velocity | None:
    """The fastest a character can be going when he Move Throughs, or None
    when he has no movement a Move Through may use.

    A movement Power bought as a purchase counts by its own meters; Running,
    Swimming and Leaping by the characteristic's total (which carries any
    power bought for it), at the best multiplier any of its purchases has."""
    from kirby_cost.model.activation import ActivationContext

    best: Velocity | None = None

    def consider(v: Velocity) -> None:
        nonlocal best
        if v.meters > 0 and (best is None or v.meters > best.meters):
            best = v

    multipliers: dict[str, int] = {}
    for section in ("powers", "equipment"):
        for obj in getattr(hero, section, None) or []:
            xmlid = (getattr(obj, "xmlid", "") or "").upper()
            if xmlid not in _MOVES or _has_modifier(obj, "MEGASCALE"):
                continue
            mult = noncombat_multiplier(obj)
            if xmlid in _CHARACTERISTIC_MOVES:
                multipliers[xmlid] = max(multipliers.get(xmlid, 0), mult)
                continue
            consider(Velocity(phase_velocity(xmlid, float(obj.levels), mult),
                              xmlid, str(obj.id)))
    for ch in getattr(hero, "characteristics", None) or []:
        xmlid = (getattr(ch, "xmlid", "") or "").upper()
        if xmlid not in _CHARACTERISTIC_MOVES:
            continue
        meters = float(hero.temporal_characteristic(
            xmlid, ActivationContext(in_hero_id=in_hero_id)))
        mult = max(noncombat_multiplier(ch), multipliers.get(xmlid, 0))
        consider(Velocity(phase_velocity(xmlid, meters, mult), xmlid, None))
    return best


__all__ = ["Velocity", "best_move_through_velocity", "noncombat_multiplier",
           "phase_velocity"]
