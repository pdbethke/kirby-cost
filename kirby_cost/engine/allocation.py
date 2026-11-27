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

import contextlib
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
# ``levels`` is their sum.  6E1 p.406 (the worked example): 9 points into 15 PD/15 ED
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
    if not _is_power(power):
        # Skill Levels or a Talent bought in a slot: no dice or distance to
        # step through, so the slot is off or as bought.
        raise NotLadderable(
            f"{getattr(power, 'xmlid', power)!r} is not a power; its slot is off or as bought")
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


@contextlib.contextmanager
def _bought_on(hero):
    """Make ``hero`` the engine's active hero for the reads inside, then
    restore whatever was active.

    A display can read the hero a power is bought on (an HKA's "w/STR"
    bracket is HD's own words, worked from his STR), and kirby-cost keeps
    that hero process-wide (`EngineContext`). A process holding many heroes
    (a fight) would otherwise word a rung after whichever was loaded last.
    """
    from kirby_cost.core.context import EngineContext

    prior = EngineContext.active_hero()
    EngineContext.set_active_hero(hero)
    try:
        yield
    finally:
        EngineContext.set_active_hero(prior)


def ladder(power, *, hero) -> list[LevelFit]:
    """Every breakpoint from nothing to the power as bought, ascending by
    Active Points, one step per distinct cost.

    ``hero`` is the hero the power is bought on, or None for a power on no
    hero; it is bound as the active hero while the steps are priced and
    worded, so the words never depend on which hero was loaded last."""
    with _bought_on(hero):
        return _ladder(power)


def _ladder(power) -> list[LevelFit]:
    # At equal cost the points buy the MOST levels (a level_value > 1 power
    # rounds its unit count up, so 5 and 6 can cost the same); at equal levels
    # the whole-die step beats the half-die one.
    seen: dict[int, LevelFit] = {}
    for step in _steps(power):
        held = seen.get(step.active_points)
        if held is None or (step.levels, not step.half_die) > (held.levels, not held.half_die):
            seen[step.active_points] = step
    return [seen[ap] for ap in sorted(seen)]


def levels_within(power, active_points: int, *, hero) -> LevelFit:
    """The largest step of ``power`` costing no more than ``active_points``.
    ``hero`` as for `ladder`."""
    fits = [s for s in ladder(power, hero=hero) if s.active_points <= active_points]
    if not fits:
        raise ValueError(f"no step of the power fits {active_points} points")
    return fits[-1]


def step_display(power, *, hero) -> str:
    """What ``power`` reads as, in HD's own words: its name and its damage
    display (``Blast 6d6``, ``Flight 30m``, ``Power Defense 5 points``);
    for a power bought as a defence split its levels (``Resistant
    Protection 3 PD/3 ED``, 6E1 p.406); for a characteristic its signed
    levels (``+5 PD``), as HD's column 2 writes them; for Skill Levels or a
    Talent bought in a slot, HD's column-2 words without the name or
    Limitations (``+1 with Block``).

    Asked of a rung's copy (`LevelFit.power`) or of a slot as bought, so a
    menu that offers a share of a Multipower reserve can say what the share
    buys without composing any of it itself. Only joins what the power
    already says. ``hero`` as for `ladder`: the words are read with him as
    the active hero, and whoever was active before is restored.
    """
    with _bought_on(hero):
        return _step_display(power)


def _is_power(obj) -> bool:
    """True for a Power or a Characteristic: the purchases a slot can step."""
    from kirby_cost.objects.characteristics.characteristic import Characteristic
    from kirby_cost.objects.powers.power import Power

    return isinstance(obj, (Power, Characteristic))


def _column2_words(obj, *, advantages: bool) -> str:
    """HD's column-2 words for a slot without its name or Limitations, and
    with its Advantages only when ``advantages`` is set. Read off a copy,
    so the slot itself is untouched; the copy is also detached from the
    reserve, whose own Limitations column 2 would otherwise print on every
    slot."""
    dup = _clone(obj)
    dup._name = ""
    dup._assigned_modifiers = ([m for m in dup._assigned_modifiers if not m.is_limitation]
                               if advantages else [])
    dup.parent = None
    return dup.column2_output.strip()


def slot_words(power, *, hero) -> str:
    """What a slot IS, in HD's own column-2 words, to tell it from the
    slots beside it: the purchase with its Advantages, without its name,
    its Limitations or the reserve's (``Blast 6d6, Reduced Endurance (0 END;
    +1/2)``, ``Entangle 3d6, 6 PD/6 ED``, ``+45 STR``).

    `step_display` says what a rung buys and leaves the Advantages out; two
    slots that are the same power at the same dice differ only in them.
    ``hero`` as for `ladder`.
    """
    with _bought_on(hero):
        return _column2_words(power, advantages=True)


def _step_display(power) -> str:
    from kirby_cost.objects.characteristics.characteristic import Characteristic

    if not _is_power(power):
        return _column2_words(power, advantages=False)
    if isinstance(power, Characteristic):
        # A characteristic bought in a slot: HD writes its amount in column 2
        # ("+20 PD"); Running, Leaping and Swimming have a distance instead.
        if power.damage_display:
            return f"{power.display} {power.damage_display}"
        return f"{power.levels_display()} {power.display}"
    parts = (power.display, power.damage_display, power.defence_levels_display())
    return " ".join(p for p in parts if p)


# -- Which slots can be on together (6E1 401, 404-405, 410, 411, 413) ---------

@dataclass(frozen=True)
class Share:
    """One slot on at one share of its framework's points.

    ``power`` is what the share buys: the slot itself when on as bought, a
    re-levelled copy (`LevelFit.power`) when a Variable slot is given less.
    """

    framework: object
    slot: object
    points: int
    power: object


def _framework(obj):
    """The Multipower or VPP holding ``obj``, or None."""
    from kirby_cost.objects.frameworks.multipower import Multipower
    from kirby_cost.objects.frameworks.vpp import VariablePowerPool

    parent = getattr(obj, "parent", None)
    return parent if isinstance(parent, (Multipower, VariablePowerPool)) else None


def pool_of(obj) -> int | None:
    """The points ``obj``'s framework can have on at once: a Multipower's
    reserve, its base cost before Advantages (6E1 404); a VPP's Pool, in
    Real Points (6E1 411). None when ``obj`` is in neither."""
    from kirby_cost.objects.frameworks.vpp import VariablePowerPool

    fw = _framework(obj)
    if fw is None:
        return None
    if isinstance(fw, VariablePowerPool):
        return int(round(fw.pool_cost))
    return int(round(fw.base_cost))


def shares(slot, *, hero) -> list[Share]:
    """Every share of its framework's points ``slot`` can be on at,
    ascending; [] when it is in no Multipower or VPP.

    * A Fixed Multipower slot is always allocated its full Active Points
      (6E1 404).
    * A Variable one may be given any share up to them, and holds what
      that share buys (6E1 405): one share per step of `ladder` above
      nothing. A slot with no steps (Skill Levels, a Compound Power) is on
      as bought.
    * A VPP power is in the Pool at its Real Points, as built (6E1 413).

    ``hero`` as for `ladder`.
    """
    from kirby_cost.objects.frameworks.vpp import VariablePowerPool

    from kirby_cost.util.rounder import round_half_down

    fw = _framework(slot)
    if fw is None:
        return []
    # .5 rounds in the character's favour (6E1 14): a smaller share.
    if isinstance(fw, VariablePowerPool):
        return [Share(fw, slot, round_half_down(slot.real_cost_pre_list), slot)]
    full = Share(fw, slot, round_half_down(slot.active_cost), slot)
    if slot.ultra:
        return [full]
    try:
        steps = ladder(slot, hero=hero)
    except NotLadderable:
        return [full]
    out = {}
    for step in steps:
        points = round_half_down(step.power.active_cost)
        if 0 < points < full.points:
            out[points] = Share(fw, slot, points, step.power)
    return [out[p] for p in sorted(out)] + [full]


def fits(on) -> bool:
    """Whether the shares ``on`` can all be on at once: per framework, their
    points within its reserve or Pool (6E1 404-405, 413). Slots of different
    frameworks never compete (6E1 401). A slot named twice is one slot, so
    it must be named at one share (6E1 410: allocated once a Phase)."""
    allocated: dict[int, int] = {}
    for share in on:
        held = allocated.setdefault(id(share.slot), share.points)
        if held != share.points:
            # One slot, one allocation a Phase (6E1 410).
            return False
    used: dict[int, int] = {}
    seen: set[int] = set()
    for share in on:
        if id(share.slot) in seen:
            continue
        seen.add(id(share.slot))
        key = id(share.framework)
        used[key] = used.get(key, 0) + share.points
        if used[key] > pool_of(share.slot):
            return False
    return True
