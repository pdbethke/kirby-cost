"""Characteristic.column2_output, ported from HD.

Half of everything wrong with the engine's display output was this one method:
14,217 of the 27,354 mismatched ``column2_output`` strings across the corpus
belonged to Characteristic, because it inherited GenericObject's default — the
alias, and nothing else. HD writes ``+0 DEX`` where this wrote ``DEX``.

Ported from ``Characteristic.getColumn2Output`` (Characteristic.java:1006).
The clauses, in HD's order, each pinned below:

* A characteristic bought at 0 levels purely to carry modifiers reads as the
  modifiers "applied to" it, with a leading comma stripped.
* Otherwise: an explicit sign, the levels, the alias.
* The player's own NAME, when set, italicised in front.
* INPUT after a colon.
* The selected option in parentheses, with the adders folded in after a
  semicolon; or the adders alone in parentheses when there is no option.
* The modifiers, unbracketed, straight on the end.
* An END-reserve note, only when the character actually has an Endurance
  Reserve to draw on.
* "(Modifiers affect Base Characteristic)" last.
"""
from __future__ import annotations

import pytest

from kirby_cost.objects.characteristics.characteristic import Characteristic


def _char(alias="DEX", levels=0, modifier_string="", adder_string="", **kw):
    """A characteristic with its rendered children stubbed.

    ``modifier_string`` and ``adder_string`` are read-only properties on
    GenericObject, and what they'd return here depends on the whole modifier
    port. These tests are about how column2_output ASSEMBLES those pieces, so
    the pieces are given directly, through a throwaway subclass — the only way
    to override a property on an instance.
    """
    cls = type("StubbedCharacteristic", (Characteristic,), {
        "modifier_string": property(lambda self: modifier_string),
        "adder_string": property(lambda self: adder_string),
    })
    c = cls("DEX")
    c._alias = alias
    c.levels = levels
    for k, v in kw.items():
        setattr(c, k, v)
    return c


def _base_modified(alias, levels, modifier_string):
    """A characteristic whose modifiers apply to its BASE.

    `add_modifiers_to_base` is gated on `is_power` in both engines — HD returns
    false outright for a non-power (Characteristic.java:96-102) and this port
    mirrors it. So the flag alone is not enough to reach that branch; the
    characteristic has to have been bought as a power, which is exactly the
    case the branch exists for.
    """
    c = _char(alias, levels, modifier_string=modifier_string)
    c._is_power = True
    c.add_modifiers_to_base = True
    return c


def test_plain_characteristic_states_sign_levels_and_alias():
    """The default case, and the one that was wrong 14,217 times."""
    assert _char("DEX", 0).column2_output == "+0 DEX"
    assert _char("STR", 15).column2_output == "+15 STR"


def test_a_negative_buy_carries_its_own_sign():
    """`getLevels() >= 0 ? "+" : ""` — the minus comes from the number."""
    assert _char("DEX", -3).column2_output == "-3 DEX"


def test_the_players_own_name_leads_in_italics():
    c = _char("STR", 10)
    c._name = "Mighty Thews"
    assert c.column2_output == "<i>Mighty Thews:</i>  +10 STR"


def test_input_follows_a_colon():
    c = _char("INT", 5)
    c.input = "Tactical"
    assert c.column2_output == "+5 INT:  Tactical"


def test_modifiers_affecting_base_are_announced():
    c = _base_modified("CON", 4, "")
    assert c.column2_output.endswith(" (Modifiers affect Base Characteristic)")


def test_zero_levels_bought_only_to_carry_modifiers_reads_as_applied_to():
    """HD's first branch: no levels, modifiers on the base, so the sentence
    turns around — the modifiers are the subject and the characteristic is
    what they are applied TO."""
    c = _base_modified("STR", 0, ", Reduced Endurance (0 END; +1/2)")
    out = c.column2_output
    assert out == "Reduced Endurance (0 END; +1/2) applied to STR", out
    assert not out.startswith(","), "the leading comma must be stripped"


def test_applied_to_form_still_leads_with_the_name():
    c = _base_modified("STR", 0, ", Only In Hero ID (-1/4)")
    c._name = "Bracers"
    assert c.column2_output == "<i>Bracers:</i>  Only In Hero ID (-1/4) applied to STR"


def test_modifiers_are_appended_unbracketed():
    c = _char("PD", 6, modifier_string=", Resistant (+1/2)")
    assert c.column2_output == "+6 PD, Resistant (+1/2)"


def test_adders_are_parenthesised_when_there_is_no_option():
    c = _char("RUNNING", 2, adder_string="x2 Noncombat")
    assert c.column2_output == "+2 RUNNING (x2 Noncombat)"
