"""Damage-class arithmetic.

**Anything that derives cost or dice belongs to this engine.** A consumer acts
on the numbers it is given; it does not work them out again. This module holds
the dice derivations a combat layer needs and used to compute for itself.

The one that prompted it: kirby-combat carried its own `STR // 5`, which drops
the half-die a remainder above 2 buys. The two answers disagreed on 22 of 56
STR values, and 9 of 107 corpus villains were rolled short -- STR 13 is
2 1/2d6 by the engine and was 2d6 in combat. Both answers looked plausible,
which is what made it dangerous.
"""
from __future__ import annotations

NORMAL = "normal"
KILLING = "killing"


def str_damage_classes(strength: int) -> int:
    """Damage Classes a given STR contributes: one per 5 points (6E1 p137)."""
    return max(strength, 0) // 5


def strike_dice(strength: int) -> tuple[int, bool]:
    """A bare Strike's dice for a given STR, as (full d6, half d6).

    The same arithmetic `Strength.damage_dice` reports for a loaded
    characteristic, reachable from a plain number for callers that hold the
    STR value rather than the object.
    """
    strength = max(strength, 0)
    return strength // 5, (strength % 5) >= 3


def augment_with_str(full_dice: int, half_die: bool, damage_type: str,
                     strength: int) -> tuple[int, bool]:
    """An attack's dice after adding STR, as (full d6, half d6).

    HERO 6E, 6E1 p137 -- adding STR to a STR-using attack:

      * Each 5 STR adds 1 Damage Class.
      * Normal damage: 1 DC = 1d6.
      * Killing damage: 1 DC = 1/2d6.
      * The Doubling Rule: a character may add no more DCs from STR than the
        attack's own base DCs. A 1d6 (3 DC) HKA therefore accepts at most 3 DC
        of STR, reaching 1d6 + 1 1/2d6.

    An attack that does not use STR, or a wielder with none, is returned
    unchanged.
    """
    if strength <= 0 or damage_type not in (NORMAL, KILLING):
        return full_dice, half_die

    added = str_damage_classes(strength)
    if damage_type == NORMAL:
        # A half-die on normal damage is +1 STUN, not a Damage Class, so it
        # does not count toward the base the Doubling Rule caps against.
        return full_dice + min(added, full_dice), half_die

    # Killing damage counts in half-die steps: 1 DC == 1 step == 5 Active Points.
    steps = full_dice * 2 + (1 if half_die else 0)
    steps += min(added, steps)
    return steps // 2, bool(steps % 2)
