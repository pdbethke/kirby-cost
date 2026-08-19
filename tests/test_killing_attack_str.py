"""KillingAttackHTH damage display — the STR that gets added to a Killing Attack.

HD prints an HKA as ``Killing Attack - Hand-To-Hand 1d6 (3d6 w/STR)``: the
dice bought, then what they become once the character's own STR is added.
This engine printed only the first half. The port carried a stub reading
"For now, skip STR bonus calculation", and it could not have worked anyway —
the block needs the active hero, which `_get_active_hero` did not return
until 2026-08-19.

The bracket is not shown just because STR exists. HD shows it only when STR
actually CHANGES the damage, or when the primary and secondary figures
disagree with each other — a character whose STR is boosted by a power has
two answers and HD prints both, slashed.
"""
from __future__ import annotations

import pytest

from kirby_cost.objects.powers.killing_attack_hth import KillingAttackHTH, _is_6e


def _hka() -> KillingAttackHTH:
    return KillingAttackHTH()


# ── the bracket's own dice renderer ────────────────────────────────────

@pytest.mark.parametrize("pips,minus,expected", [
    (9,  0, "3d6"),
    (10, 0, "3d6+1"),
    (11, 0, "3 1/2d6"),
    (3,  0, "1d6"),
    (1,  0, "d6+1"),      # no whole dice: HD omits the leading count
    (2,  0, "1/2d6"),
])
def test_pips_render_as_hd_writes_them(pips, minus, expected):
    assert _hka()._dice(pips, minus) == expected


def test_a_minus_one_pip_attack_counts_down_from_the_next_die():
    """With a MINUSONEPIP adder a two-pip remainder is not "1/2d6" — HD
    counts down from the next whole die instead."""
    assert _hka()._dice(11, 1) == "4d6 - 1"


def test_the_secondary_figure_spaces_that_subtraction_differently():
    """Not a rule, just what HD's two branches say: the primary figure gets
    "d6 - 1" and the secondary "d6-1". Pinned because it looks like a typo
    and would otherwise be "tidied" into a mismatch."""
    assert _hka()._dice(11, 1, tight=True) == "4d6-1"


# ── when the bracket appears at all ────────────────────────────────────

def test_no_strength_bonus_leaves_the_figures_untouched():
    """NOSTRBONUS says the attack never adds STR, so the four figures come
    back exactly as they went in and the caller prints no bracket."""
    from kirby_cost.objects.modifier import Modifier
    hka = _hka()
    mod = Modifier(); mod.xmlid = "NOSTRBONUS"
    hka._assigned_modifiers = [mod]
    assert hka._add_strength(9, 0, 9, 9, 9, 9) == (9, 9, 9, 9)


def test_an_unreadable_strength_minimum_is_treated_as_no_bonus():
    """HD parses the STR MINIMUM option's alias as a number and CATCHES the
    failure, treating an unreadable minimum as NOSTRBONUS rather than as
    zero. A minimum it cannot read is not a minimum of none."""
    from kirby_cost.objects.modifier import Modifier
    from kirby_cost.objects.adder import Adder
    hka = _hka()
    mod = Modifier(); mod.xmlid = "STRMINIMUM"
    opt = Adder(); opt._alias = "not a number"
    mod._selected_option = opt
    hka._assigned_modifiers = [mod]
    assert hka._add_strength(9, 0, 9, 9, 9, 9) == (9, 9, 9, 9)


def test_a_strength_minimum_with_no_option_is_also_no_bonus():
    from kirby_cost.objects.modifier import Modifier
    hka = _hka()
    mod = Modifier(); mod.xmlid = "STRMINIMUM"
    hka._assigned_modifiers = [mod]
    assert hka._add_strength(9, 0, 9, 9, 9, 9) == (9, 9, 9, 9)


# ── the edition switch ─────────────────────────────────────────────────

class _Hero:
    def __init__(self, tid): self.original_template_id = tid


def test_every_named_6e_template_reads_as_6e():
    for tid in ("builtIn.Main6E.hdt", "builtIn.Vehicle6E.hdt",
                "builtIn.Automaton6E.hdt", "builtIn.Computer6E.hdt"):
        assert _is_6e(_Hero(tid)) is True


def test_a_character_declaring_no_template_is_costed_as_6e():
    """It falls back to the Main6E bootstrap, which is 6E — so the unknown
    case answers True. Answering False would silently re-enable the 5E cap
    that stops STR from more than doubling an attack's dice."""
    assert _is_6e(_Hero(None)) is True


def test_a_5e_template_does_not():
    assert _is_6e(_Hero("builtIn.Main5E.hdt")) is False
