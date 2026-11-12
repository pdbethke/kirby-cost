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
            copies = [_clone(k) for k in kids]
            for kid, kid_dup in zip(kids, copies):
                # A child that pointed at ``node`` points at its copy; one
                # that pointed elsewhere (or nowhere) keeps doing so.
                if getattr(kid, "parent", None) is node:
                    kid_dup.parent = dup
            setattr(dup, attr, copies)
    return dup


# Resistant Protection (FORCEFIELD) is bought as a split across these fields;
# ``levels`` is their sum.  6E1 p.406 (Kerendor): 9 points into 15 PD/15 ED
# gives 3 PD/3 ED.
_SPLIT_FIELDS = ("pd_levels", "ed_levels", "md_levels", "powd_levels")


def _split(power) -> dict[str, int]:
    """The defence level fields the power was bought with (empty if none)."""
    return {f: int(getattr(power, f, 0) or 0) for f in _SPLIT_FIELDS
            if int(getattr(power, f, 0) or 0) > 0}


def _fit(power, levels: int, drop_half: bool, fields: dict | None = None) -> LevelFit:
    dup = _clone(power)
    held = [a for a in dup._assigned_adders if a.xmlid in _HALF_ADDERS]
    if drop_half:
        dup._assigned_adders = [a for a in dup._assigned_adders if a not in held]
    dup.levels = levels
    for name, value in (fields or {}).items():
        setattr(dup, name, value)
    return LevelFit(power=dup, levels=levels,
                    half_die=bool(held) and not drop_half,
                    active_points=int(round(dup.active_cost)),
                    display=dup.damage_display)


def _steps(power) -> list[LevelFit]:
    if (power.level_cost and not (power.levels or 0) > 0
            and any(a.xmlid in _HALF_ADDERS for a in power.assigned_adders)):
        # Bought as 0 levels plus a +1/2d6 / +1 pip adder (a 1/2d6 killing
        # attack): there is no whole die to step, so the slot is nothing or
        # as bought (6E1 p.405: any share from 0 to its Active Points).
        return [_fit(power, 0, True), _fit(power, 0, False)]
    if not power.level_cost or not (power.levels or 0) > 0:
        raise NotLadderable(
            f"{getattr(power, 'xmlid', power)!r} is not priced by levels")
    has_half = any(a.xmlid in _HALF_ADDERS for a in power.assigned_adders)
    top = int(power.levels)
    bought = _split(power)
    if bought:
        return _split_steps(power, bought, top)
    out = [_fit(power, 0, True)]
    for n in range(1, top + 1):
        if has_half:
            out.append(_fit(power, n, True))
        out.append(_fit(power, n, False))
    return out


def _split_steps(power, bought: dict[str, int], top: int) -> list[LevelFit]:
    """Steps of a multi-level defence: every field at the same fraction of
    its bought value, floored.  Floored fields can sum to less than the
    fraction's share of ``levels``, so ``levels`` is re-summed from the
    fields (except at the top); the engine then prices that, and ``ladder`` keeps what fits.
    Flash Defense is an adder, not a defence field, and stays as bought."""
    out, seen = [], set()
    for n in range(top + 1):
        fields = {name: v * n // top for name, v in bought.items()}
        key = tuple(fields.values())
        if key in seen:
            continue
        seen.add(key)
        # The top step is the power as bought: ``levels`` may differ from the
        # field sum, so it is not re-summed there.
        levels = int(power.levels) if n == top else sum(fields.values())
        out.append(_fit(power, levels, True, fields))
    return out


def ladder(power) -> list[LevelFit]:
    """Every breakpoint from nothing to the power as bought, ascending by
    Active Points, one step per distinct cost."""
    # At equal cost the points buy the MOST levels (a level_value > 1 power
    # rounds its unit count up, so 5 and 6 can cost the same); at equal levels
    # the whole-die step beats the half-die one.
    seen: dict[int, LevelFit] = {}
    for step in _steps(power):
        held = seen.get(step.active_points)
        if held is None or (step.levels, not step.half_die) > (held.levels, not held.half_die):
            seen[step.active_points] = step
    return [seen[ap] for ap in sorted(seen)]


def levels_within(power, active_points: int) -> LevelFit:
    """The largest step of ``power`` costing no more than ``active_points``."""
    fits = [s for s in ladder(power) if s.active_points <= active_points]
    if not fits:
        raise ValueError(f"no step of the power fits {active_points} points")
    return fits[-1]
