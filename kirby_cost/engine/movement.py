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
* A movement bought as a Multipower or VPP slot is there only while the slot
  holds its share of the framework's points (6E1 404-405, 413), so each
  velocity names the shares it needs (`Velocity.shares`), and a
  characteristic total carrying slots is offered with every set of them the
  frameworks can hold at once.
* Leaping differs (6E1 245): a Noncombat leap covers its multiple of the
  distance, but its duration in Phases equals the number of doublings. Its
  velocity per Phase is that distance over those Phases.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

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
    #: The framework shares it needs on (`engine.allocation.Share`); () for
    #: movement in no Multipower or VPP.
    shares: tuple = field(compare=False)


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
    """The fastest a character can be going when he Move Throughs, framework
    or not, or None when he has no movement a Move Through may use."""
    found = move_through_velocities(hero, in_hero_id=in_hero_id)
    return max(found, key=lambda v: v.meters) if found else None


def _in_total(obj) -> bool:
    return bool(getattr(obj, "affects_primary", False) or getattr(obj, "affects_total", False))


def move_through_velocities(hero, *, in_hero_id: bool) -> list[Velocity]:
    """Every velocity a Move Through may bring, each with the framework
    shares it needs; none of 0m.

    A movement Power counts by its own meters, a Variable slot at each share
    (6E1 405). Running, Swimming and Leaping count by the characteristic's
    total, at the best multiplier any purchase in it has; when the total
    carries framework slots, it is offered with every set of them that fits
    on at once, each at each of its shares, none included."""
    from kirby_cost.engine.allocation import fits, shares
    from kirby_cost.model.activation import ActivationContext

    out: list[Velocity] = []

    def add(meters: float, xmlid: str, hd_id, on: tuple) -> None:
        if meters > 0:
            out.append(Velocity(meters, xmlid, hd_id, on))

    multipliers: dict[str, int] = {}
    slots: dict[str, list] = {}
    for section in ("powers", "equipment"):
        for obj in getattr(hero, section, None) or []:
            xmlid = (getattr(obj, "xmlid", "") or "").upper()
            if xmlid not in _MOVES or _has_modifier(obj, "MEGASCALE"):
                continue
            held = shares(obj, hero=hero)
            if xmlid in _CHARACTERISTIC_MOVES:
                if held and _in_total(obj):
                    slots.setdefault(xmlid, []).append((obj, held))
                elif not held:
                    multipliers[xmlid] = max(multipliers.get(xmlid, 0),
                                             noncombat_multiplier(obj))
                continue
            for share in held or [None]:
                power = share.power if share else obj
                add(phase_velocity(xmlid, float(power.levels), noncombat_multiplier(power)),
                    xmlid, str(obj.id), (share,) if share else ())
    for ch in getattr(hero, "characteristics", None) or []:
        xmlid = (getattr(ch, "xmlid", "") or "").upper()
        if xmlid not in _CHARACTERISTIC_MOVES:
            continue
        total = float(hero.temporal_characteristic(
            xmlid, ActivationContext(in_hero_id=in_hero_id)))
        mine = slots.get(xmlid, [])
        bare = total - sum(float(obj.levels) for obj, _ in mine)
        mult = max(noncombat_multiplier(ch), multipliers.get(xmlid, 0))
        # Any set of its slots the frameworks hold at once (6E1 404: no
        # number limit, only the points), each at any of its shares.
        for pick in itertools.product(*[[None] + held for _, held in mine]):
            on = tuple(s for s in pick if s is not None)
            if not fits(on):
                continue
            meters = bare + sum(float(s.power.levels) for s in on)
            best_mult = max([mult] + [noncombat_multiplier(s.power) for s in on])
            add(phase_velocity(xmlid, meters, best_mult), xmlid, None, on)
    return out


__all__ = ["Velocity", "best_move_through_velocity", "move_through_velocities",
           "noncombat_multiplier", "phase_velocity"]
