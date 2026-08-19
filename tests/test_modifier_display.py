"""Modifier.get_fraction and Modifier.column2_output, ported from HD.

``GenericObject.modifier_string`` was the deliberate stub at the centre of the
display gap — its own docstring named what it was waiting for: "the port's
``Modifier`` has neither ``column2_output`` nor ``is_limitation``, so a partial
port would emit confidently wrong strings."

Half of that is now stale. ``is_limitation`` exists (a field, set from the
template). ``column2_output`` exists too, but only as GenericObject's default —
the alias, the input, the comments — where HD renders the whole parenthetical
that makes a modifier readable: ``Resistant (+1/2)``, ``Only In Hero ID
(-1/4)``, ``Reduced Endurance (0 END; +1/2)``.

The value inside those brackets comes from ``getFraction``
(Modifier.java:532), which is not a general decimal-to-fraction helper. It
carries an explicit sign always, snaps to quarters by nearest match, rolls a
value within a quarter of 1 up into the whole number, and has a separate
multiplier form ("x2", "x1/2"). GenericObject.fraction — which already exists —
does none of that and is not a substitute.
"""
from __future__ import annotations

import pytest

from kirby_cost.objects.modifier import Modifier


def _mod(alias="", value=0.0, **kw):
    m = Modifier()
    m._alias = alias
    m._base_cost = value
    for k, v in kw.items():
        setattr(m, k, v)
    return m


# ── getFraction ────────────────────────────────────────────────────────

@pytest.mark.parametrize("value,expected", [
    (0.5, "+1/2"),
    (0.25, "+1/4"),
    (0.75, "+3/4"),
    (-0.25, "-1/4"),
    (-0.5, "-1/2"),
    (1.0, "+1"),
    (-1.0, "-1"),
    (1.5, "+1 1/2"),
    (-1.25, "-1 1/4"),
    (2.0, "+2"),
])
def test_fraction_signs_and_quarters(value, expected):
    """An advantage always shows its plus; a limitation always its minus."""
    assert _mod().get_fraction(value) == expected


def test_zero_is_plus_zero_for_an_advantage_and_minus_zero_for_a_limitation():
    """HD distinguishes them (Modifier.java:539-545), and the sign is the only
    thing carrying the distinction when the value is nothing."""
    advantage = _mod()
    advantage.is_limitation = False
    assert advantage.get_fraction(0) == "+0"

    limitation = _mod()
    limitation.is_limitation = True
    assert limitation.get_fraction(0) == "-0"


def test_a_value_within_a_quarter_of_the_next_whole_rounds_up_to_it():
    """`Math.abs(1 - val) < closest` — 0.9 is nearer 1 than 3/4, so HD prints
    "+1" rather than "+3/4"."""
    assert _mod().get_fraction(0.9) == "+1"


# ── column2_output ─────────────────────────────────────────────────────

def test_a_plain_modifier_is_alias_then_value_in_brackets():
    m = _mod("Resistant", 0.5)
    assert m.column2_output == "Resistant (+1/2)"


def test_a_limitation_carries_its_minus():
    m = _mod("Only In Hero ID", -0.25)
    assert m.column2_output == "Only In Hero ID (-1/4)"


def test_an_alias_that_already_opens_a_bracket_continues_it():
    """HD counts unbalanced parens in what it has built and, if one is open,
    joins with "; " instead of opening a second (Modifier.java:440-453)."""
    m = _mod("Reduced Endurance (0 END", 0.5)
    assert m.column2_output == "Reduced Endurance (0 END; +1/2)"


def test_the_option_alias_follows_the_modifier_alias():
    m = _mod("Reduced Endurance", 0.5)
    m.show_option_in_parens = False
    m._selected_option = _mod("0 END")
    m._selected_option.display_in_string = True
    assert m.column2_output == "Reduced Endurance 0 END (+1/2)"


def test_comments_go_inside_the_brackets_with_the_value():
    """The Java says so in as many words: "Comments are placed inside the
    parentheses, with the value.\""""
    m = _mod("Restrainable", -0.5)
    m.comments = "only by magic"
    assert m.column2_output == "Restrainable (only by magic; -1/2)"
