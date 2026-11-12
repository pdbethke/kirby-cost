"""Price a power at a smaller allocation of a Multipower reserve.

6E1 p.405-406: a Multipower slot may be bought at less than its full
allocation, and the slot then holds as many levels as fit in the points
given (Drain 6d6 at 40 points is 4d6; a 12d6 Blast in a 20-point share is
4d6; Flight 50m with Reduced Endurance in 30 points is 24m, the +1/4
paid out of the allocation).  The slot's own Advantages stay on the power
and are priced in; the reserve's Advantages are skipped by the cost engine
(``cost.py``, 6E1 p.407), and ``parent`` is kept so that stays true.

Cost always comes from the engine: each candidate is a re-levelled COPY
whose ``active_cost`` is read live.  The copy owns its modifier and adder
lists because ``_compute_active_cost`` re-parents every assigned modifier
onto the power it is costing; sharing the original's would silently move
them onto the copy.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

_HALF_ADDERS = ("PLUSONEHALFDIE", "PLUSONEPIP")


class NotLadderable(ValueError):
    """The power's cost is not driven by ``levels``, so it has no steps."""


@dataclass(frozen=True)
class LevelFit:
    power: object          # a re-levelled, re-costed COPY; never the original
    levels: int            # 0 = nothing of the power
    half_die: bool         # True when the step carries the slot's own +1/2d6 / +1 pip adder
    active_points: int     # the copy's active_cost (the slot's own Advantages included)
    display: str           # the copy's damage_display (dice, metres, ...)


def _clone(node):
    """Copy a power/modifier/adder with its own child lists, recursively."""
    dup = copy.copy(node)
    for attr in ("_assigned_modifiers", "_assigned_adders"):
        kids = getattr(node, attr, None)
        if kids is not None:
            setattr(dup, attr, [_clone(k) for k in kids])
    return dup


def _fit(power, levels: int, drop_half: bool) -> LevelFit:
    dup = _clone(power)
    held = [a for a in dup._assigned_adders if a.xmlid in _HALF_ADDERS]
    if drop_half:
        dup._assigned_adders = [a for a in dup._assigned_adders if a not in held]
    dup.levels = levels
    return LevelFit(power=dup, levels=levels,
                    half_die=bool(held) and not drop_half,
                    active_points=int(round(dup.active_cost)),
                    display=dup.damage_display)


def _steps(power) -> list[LevelFit]:
    if not getattr(power, "_level_cost", 0) or not (power.levels or 0) > 0:
        raise NotLadderable(
            f"{getattr(power, 'xmlid', power)!r} is not priced by levels")
    has_half = any(a.xmlid in _HALF_ADDERS for a in power.assigned_adders)
    top = int(power.levels)
    out = [_fit(power, 0, True)]
    for n in range(1, top + 1):
        if has_half:
            out.append(_fit(power, n, True))
        out.append(_fit(power, n, False))
    return out


def ladder(power) -> list[LevelFit]:
    """Every breakpoint from nothing to the power as bought, ascending by
    Active Points, one step per distinct cost."""
    seen: dict[int, LevelFit] = {}
    for step in _steps(power):
        seen.setdefault(step.active_points, step)
    return [seen[ap] for ap in sorted(seen)]


def levels_within(power, active_points: int) -> LevelFit:
    """The largest step of ``power`` costing no more than ``active_points``."""
    fits = [s for s in ladder(power) if s.active_points <= active_points]
    if not fits:
        raise ValueError(f"no step of the power fits {active_points} points")
    return fits[-1]
