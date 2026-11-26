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

from typing import NamedTuple

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


class Dice(NamedTuple):
    """An attack's damage dice: whole dice, a half die, and HD's pip adders.

    ``minus_one`` is HD's MINUSONEPIP, whose alias is "+1d6 -1": ``full``
    already counts the die it adds, and the pip comes off. Every field is
    required -- a missing adder is a decision, not a default.
    """

    full: int
    half: bool
    plus_one: bool
    minus_one: bool


def _require_type(damage_type: str) -> None:
    if damage_type not in (NORMAL, KILLING):
        raise ValueError(
            f"no Damage Class Table column for damage type {damage_type!r}; "
            f"this table covers {NORMAL!r} and {KILLING!r} (6E2 p.99)"
        )


def damage_classes(dice: Dice, damage_type: str) -> int:
    """How many Damage Classes these dice are (6E2 p.99).

    Normal Damage: one per whole die. A half die is not a Damage Class
    (6E2 p.101: "there's no such thing as a 'half Damage Class'"), and a
    "+1d6 -1" counts as the die below it.

    Killing Damage: 5 Active Points a DC, so 3 a die, 2 for a half die, 1
    for a +1 pip, and -1 for HD's "+1d6 -1" rung (the Peacemaker's 2d6-1 is
    5 DC, the half-die's price).
    """
    _require_type(damage_type)
    if damage_type == NORMAL:
        return dice.full - (1 if dice.minus_one else 0)
    return (dice.full * 3 + (2 if dice.half else 0)
            + (1 if dice.plus_one else 0) - (1 if dice.minus_one else 0))


def dice_for(dcs: int, damage_type: str) -> Dice:
    """The dice a number of Damage Classes buys (6E2 p.99's table).

    Killing: 1 DC is +1, 2 DC is 1/2d6, 3 DC is 1d6, and so on up.
    """
    _require_type(damage_type)
    if dcs < 0:
        raise ValueError(f"a Damage Class count can't be negative: {dcs}")
    if damage_type == NORMAL:
        return Dice(full=dcs, half=False, plus_one=False, minus_one=False)
    full, rem = divmod(dcs, 3)
    return Dice(full=full, half=rem == 2, plus_one=rem == 1, minus_one=False)


def add_damage_classes(dice: Dice, damage_type: str, added: int) -> Dice:
    """These dice with ``added`` whole Damage Classes on top (6E2 p.101).

    "+1 DC for each +1 DC ... regardless of the type of damage done": a
    Martial Strike's +2 DC takes a 3d6 club to 5d6 and a 1d6 HKA sword to
    1 1/2d6. A Normal attack keeps its half die (a half die is not a DC, so
    adding DCs adds whole dice beside it); a Killing attack is re-read off
    the table at its new total.
    """
    _require_type(damage_type)
    if added < 0:
        raise ValueError(f"can't add a negative number of Damage Classes: {added}")
    if added == 0:
        return dice
    if damage_type == NORMAL:
        return dice._replace(full=dice.full + added)
    return dice_for(damage_classes(dice, KILLING) + added, KILLING)


def augment_with_str(dice: Dice, damage_type: str, strength: int) -> Dice:
    """An attack's dice after adding STR (6E1 p.137, 6E2 p.99).

      * Each full 5 STR adds 1 Damage Class (6E2 p.101: "a full 5 extra
        points of STR ... to get +1 DC").
      * The Doubling Rule: no more DCs from STR than the attack's own DCs.
        A 1d6 (3 DC) HKA takes at most 3 DC of STR, reaching 2d6.

    Killing Damage is counted in DCs, not half-die steps: STR 5 on a 1d6
    HKA is 1d6+1. Counting steps (which this did until 0.8.0) gave
    1 1/2d6, and dropped a +1 pip entirely.
    """
    _require_type(damage_type)
    if strength <= 0:
        return dice
    base = damage_classes(dice, damage_type)
    return add_damage_classes(dice, damage_type, min(str_damage_classes(strength), base))


# -- Damage Classes of a purchase (6E2 98-100) --------------------------------

from dataclasses import dataclass as _dataclass


@_dataclass(frozen=True)
class DamageAdvantage:
    """An Advantage that counts toward an attack's Damage Classes: a
    modifier XMLID, narrowed (as the book narrows it) to one of its options
    or to the modifier carrying one adder. None means any."""

    xmlid: str
    option: str | None
    adder: str | None

    def __post_init__(self) -> None:
        for field in ("xmlid", "option", "adder"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, value.upper())

    def matches(self, modifier) -> bool:
        if (getattr(modifier, "xmlid", "") or "").upper() != self.xmlid:
            return False
        if self.option is not None:
            chosen = getattr(modifier, "selected_option", None)
            if (getattr(chosen, "xmlid", "") or "").upper() != self.option:
                return False
        if self.adder is not None:
            adders = getattr(modifier, "assigned_adders", None) or []
            if not any((getattr(a, "xmlid", "") or "").upper() == self.adder
                       for a in adders):
                return False
        return True


#: The Advantages 6E2 100 says TYPICALLY "directly affect how the victim
#: takes damage", and so count toward Damage Classes -- "though the final
#: decision is up to the GM". A campaign passes this, or its own trimmed or
#: extended list, to its DAMAGE_CLASSES limit; nothing applies it unasked.
#: Usable As Attack is Usable On Others' UAA option; Boostable Charges is
#: Charges with the Boostable adder. MegaScale counts "in some instances",
#: which only the GM can name, so it is not here: a GM who counts it adds it.
BOOK_DAMAGE_ADVANTAGES: tuple[DamageAdvantage, ...] = tuple(
    DamageAdvantage(x, o, a) for x, o, a in (
        ("AOE", None, None), ("ARMORPIERCING", None, None),
        ("AVAD", None, None), ("AUTOFIRE", None, None),
        ("CHARGES", None, "BOOSTABLE"), ("CONTINUOUS", None, None),
        ("CUMULATIVE", None, None), ("DAMAGEOVERTIME", None, None),
        ("DOESBODY", None, None), ("DOESKB", None, None),
        ("DOUBLEKB", None, None), ("INCREASEDSTUNMULTIPLIER", None, None),
        ("PENETRATING", None, None), ("STICKY", None, None),
        ("TIMELIMIT", None, None), ("TRANSDIMENSIONAL", None, None),
        ("TRIGGER", None, None), ("UNCONTROLLED", None, None),
        ("UOO", "UAA", None), ("VARIABLEADVANTAGE", None, None),
        ("VARIABLESFX", None, None),
    ))


def damage_classes_of(power, counts: tuple[DamageAdvantage, ...]) -> float:
    """The Damage Classes of a purchase that does damage (6E2 98-99).

    One DC is 5 Active Points: a Blast is 1 DC a die, a Killing Attack 3, a
    Mental Blast (10 points a die) 2. Advantages count only when they
    directly affect how the victim takes damage -- the ``counts`` the GM
    names (`BOOK_DAMAGE_ADVANTAGES` is the book's typical list): Armor
    Piercing does, Reduced Endurance does not. So this is the purchase's
    Active Points with only those Advantages applied (the engine's own
    `_active_cost_where`, inheritance from a framework included), over 5.
    A purchase that does no damage (HD's ``DOESDAMAGE``) has none: asking
    raises rather than answering 0.
    """
    if not getattr(power, "does_damage", False):
        raise ValueError(f"{getattr(power, 'xmlid', power)!r} does no damage, "
                         "so has no Damage Classes")
    active = power._active_cost_where(
        lambda m: any(a.matches(m) for a in counts))
    return active / 5.0
