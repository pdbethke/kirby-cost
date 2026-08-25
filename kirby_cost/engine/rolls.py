"""Characteristic rolls.

The 3d6 target a characteristic grants. Lives here for the same reason the
dice do: it follows from the BUILD, and the campaign's rules can move both
constants, so a consumer that hardcodes them is answering a question it cannot
see all of.

`Characteristic.roll_value` is the accessor when you hold the object. This
module is for callers that hold only the number -- kirby-combat's mental
actions carry a flat `ego`, not a characteristic.
"""
from __future__ import annotations

from kirby_cost.util.rounder import round_half_up

#: 6E defaults. A campaign states its own through Rules; pass them in when the
#: hero is to hand rather than assuming these.
DEFAULT_BASE = 9
DEFAULT_DENOMINATOR = 5.0


def characteristic_roll(value: float, *, base: int = DEFAULT_BASE,
                        denominator: float = DEFAULT_DENOMINATOR) -> int:
    """The 3d6 target for a characteristic of `value`: 9 + value/5.

    **The division is ROUNDED, not truncated.** That is the whole reason this
    function exists: kirby-combat carried `9 + CHAR // 5` in three places, and
    the two disagree on 16 of 40 characteristic values -- an INT of 13 rolls
    12-, not 11-, and an EGO of 18 defends at 13-, not 12-.
    """
    return int(base + round_half_up(value / denominator))


def roll_constants(active_hero=None) -> tuple[int, float]:
    """This campaign's (base, denominator), or the 6E defaults."""
    rules = getattr(active_hero, "rules", None) if active_hero is not None else None
    if rules is None:
        return DEFAULT_BASE, DEFAULT_DENOMINATOR
    return rules.char_roll_base, rules.char_roll_denominator
