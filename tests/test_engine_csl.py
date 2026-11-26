"""Which attacks a Combat Skill Level reaches (6E1 72), lifted from kirby-combat.

6E1 72 prices a level by its breadth: with any single attack, a small group,
a large group, HTH Combat, Ranged Combat, All Attacks. HD stores no link from a
narrow level to the attacks it names; the words are in its NAME or its
OPTION_ALIAS. So a narrow level is matched by those words, and when the words
match nothing on the build the answer is UNKNOWN: never a guess either way
(workshop plan 1b, R14).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from kirby_cost.engine.csl import Breadth, Reach, breadth_of, named_text, reach_on
from tests.corpus import require_authored_hdc


def _level(option, name="", alias=None):
    opt = SimpleNamespace(xmlid=option, alias=alias)
    return SimpleNamespace(xmlid="COMBAT_LEVELS", name=name, _selected_option=opt,
                           option_id=option)


def test_breadth_is_the_option_hd_records():
    assert breadth_of(_level("TIGHT")) is Breadth.TIGHT
    assert breadth_of(_level("ALL")) is Breadth.ALL


def test_an_option_that_is_not_one_of_the_six_has_no_breadth():
    assert breadth_of(_level("SOMETHINGELSE")) is None


def test_the_templates_own_wording_names_nothing():
    """"with a small group of attacks" is HD's boilerplate, not a choice."""
    assert named_text(_level("TIGHT", alias="with a small group of attacks")) == ""
    assert named_text(_level("TIGHT", name="+1 With Punch, Haymaker, and Throw",
                             alias="with a small group of attacks")) \
        == "+1 With Punch, Haymaker, and Throw"


@pytest.mark.parametrize("option,ranged,want", [
    ("ALL", True, Reach.YES), ("ALL", False, Reach.YES),
    ("HTH", False, Reach.YES), ("HTH", True, Reach.NO),
    ("RANGED", True, Reach.YES), ("RANGED", False, Reach.NO),
])
def test_a_broad_breadth_reaches_by_range(option, ranged, want):
    (answer,) = reach_on(_level(option), [(("Anything",), ranged)])
    assert answer is want


def test_a_narrow_level_reaches_the_attacks_it_names():
    """PowerLad's TIGHT level names three maneuvers; once its words find
    something on the build, an attack it does not name is a plain no."""
    level = _level("TIGHT", name="+1 With Punch, Haymaker, and Throw",
                   alias="with a small group of attacks")
    haymaker, hka = reach_on(level, [(("Haymaker",), False),
                                     (("Rending and Tearing", "Brick Tricks"), False)])
    assert haymaker is Reach.YES
    assert hka is Reach.NO


def test_a_level_bought_across_a_framework_reaches_its_slots():
    level = _level("BROAD", alias="with Power Over Light And Heat Multipower")
    (answer,) = reach_on(level, [(("Searing Ray", "Power Over Light And Heat Multipower"), True)])
    assert answer is Reach.YES


def test_a_narrow_level_whose_words_find_nothing_is_unknown():
    """Bought for something, but nothing on the build answers to its words:
    the engine cannot say what it reaches, so it says so."""
    named_nothing = _level("SINGLE", alias="with any single attack")
    unmatched = _level("SINGLE", name="+2 with my lucky right hook")
    for level in (named_nothing, unmatched):
        assert reach_on(level, [(("Blast",), True), (("Strike",), False)]) \
            == [Reach.UNKNOWN, Reach.UNKNOWN]


def test_an_unrecognised_breadth_is_unknown():
    assert reach_on(_level("ODD"), [(("Blast",), True)]) == [Reach.UNKNOWN]


def test_a_two_letter_name_cannot_match_every_sentence():
    level = _level("SINGLE", name="+1 with Ox Punch")
    assert reach_on(level, [(("Ox",), False), (("Ox Punch",), False)]) \
        == [Reach.NO, Reach.YES]


def test_powerlads_level_is_read_off_his_build():
    from kirby_cost.io.formats import load_build
    hero = load_build(str(require_authored_hdc("PowerLad")), format="hdc")
    (level,) = [p for p in hero.powers if p.xmlid == "COMBAT_LEVELS"]
    assert breadth_of(level) is Breadth.TIGHT
    assert named_text(level) == "+1 With Punch, Haymaker, and Throw"
