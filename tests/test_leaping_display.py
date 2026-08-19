"""Leaping.display_notes and column2_output, ported from HD.

Leaping does not print like the other movement characteristics. Running gives
``Running -6m (12m total)``; Leaping gives ``Leaping -2m (4m forward, 2m
upward)``, because a leap has two distances and the rules relate them:

    All characters have a base forward leap of 4m and a base upward leap of
    2m (half the forward leap).                       — 6E Volume 2, p30

The four values behind those numbers — primary/secondary forward/upward —
were already ported in leaping.py and had simply never run: the loader mapped
every characteristic to the base class, so nothing ever constructed a Leaping.
Only the formatting was missing.

The half-metre rules are the fiddly part and are HD's, not the rulebook's.
``getDisplayNotes`` (Leaping.java:801) applies a different condition to
forward than to upward, and the difference is real: a forward distance shows
"N 1/2" only when the whole part is over 1, while an upward distance of less
than a metre can print a bare "1/2m" with no leading number.
"""
from __future__ import annotations

import pytest

from kirby_cost.objects.characteristics.leaping import Leaping


def _leap(levels=0, forward=4.0, upward=2.0, sec_forward=None, sec_upward=None):
    """A Leaping whose four computed distances are given directly.

    The calculators need an active hero and walk its powers; these tests are
    about how the four numbers are FORMATTED, so they are supplied.
    """
    sec_forward = forward if sec_forward is None else sec_forward
    sec_upward = upward if sec_upward is None else sec_upward
    cls = type("StubbedLeaping", (Leaping,), {
        "get_primary_forward": lambda self, hero=None: forward,
        "get_primary_upward": lambda self, hero=None: upward,
        "get_secondary_forward": lambda self, hero=None: sec_forward,
        "get_secondary_upward": lambda self, hero=None: sec_upward,
        "modifier_string": property(lambda self: ""),
        "adder_string": property(lambda self: ""),
    })
    c = cls()
    c._alias = "Leaping"
    c.levels = levels
    return c


# ── display_notes ──────────────────────────────────────────────────────

def test_whole_distances_read_as_forward_and_upward():
    assert _leap(forward=4.0, upward=2.0).display_notes == "4m forward, 2m upward"


def test_a_character_who_cannot_leap_reads_as_zero():
    assert _leap(levels=-4, forward=0.0, upward=0.0).display_notes == "0m forward, 0m upward"


def test_a_half_metre_forward_shows_as_a_fraction():
    assert _leap(forward=4.5, upward=2.0).display_notes == "4 1/2m forward, 2m upward"


def test_a_half_metre_upward_keeps_its_zero_when_levels_are_not_negative():
    """The first branch already covers this: its condition is
    `value > 1 OR levels >= 0`, so with levels >= 0 it wins and prints
    "0 1/2m". My first version of this test asserted "1/2m" and was simply
    wrong about HD."""
    assert _leap(levels=0, forward=1.0, upward=0.5).display_notes == (
        "1m forward, 0 1/2m upward"
    )


def test_the_bare_half_upward_needs_negative_levels():
    """HD's SECOND upward branch is reachable only when the first fails —
    which needs `value <= 1` and `levels < 0` — and then requires value > 0.
    A character who sold leaping down to half a metre upward prints "1/2m"
    with no leading zero. Forward has no equivalent branch, so it still
    shows its whole part."""
    assert _leap(levels=-3, forward=0.5, upward=0.5).display_notes == (
        "0m forward, 1/2m upward"
    )


def test_primary_and_secondary_are_shown_slashed_when_they_differ():
    """A power that boosts only one of them makes the two disagree, and HD
    prints both rather than picking one."""
    notes = _leap(forward=4.0, upward=2.0, sec_forward=8.0, sec_upward=4.0).display_notes
    assert notes == "4m/8m forward, 2m/4m upward"


# ── column2_output ─────────────────────────────────────────────────────

def test_column2_is_alias_levels_and_the_notes():
    assert _leap(levels=-2, forward=4.0, upward=2.0).column2_output == (
        "Leaping -2m (4m forward, 2m upward)"
    )


def test_a_positive_buy_carries_a_plus():
    """Running and Leaping agree here: the sign is only explicit when adding."""
    assert _leap(levels=6, forward=10.0, upward=5.0).column2_output == (
        "Leaping +6m (10m forward, 5m upward)"
    )


def test_the_players_own_name_leads_in_italics():
    c = _leap(levels=6, forward=10.0, upward=5.0)
    c._name = "Bounding Stride"
    assert c.column2_output.startswith("<i>Bounding Stride:</i>  Leaping +6m")
