"""What a skill rolls against, and therefore what its roll is.

6E1 p57 divides Skills by what sets their base roll. Intellect, Agility and
Interaction Skills take theirs from a linked characteristic — nine plus a fifth
of that characteristic, rounded the engine's way. Background Skills mostly do
not; their base is the flat general one, and the template says so by naming
GENERAL. 6E1 p15 works the example: a character at DEX 20 rolls DEX at 13-.

The engine failed the first half of that. A skill names its characteristic only
inside its ``<CHARACTERISTIC_CHOICE>`` block, and the template provider read
that block for its COSTS and dropped the name, so every skill loaded as GENERAL
and every characteristic-based roll came out at the general 11-, for every
character, whatever the characteristic. Nothing caught it because the two
agreed by accident: the no-characteristic branch of ``Skill.roll_value`` uses
``Rules.general_level``, which is 10, and a defaulted characteristic is also
worth 10.

**The parity gates do not exercise this.** Every .hdc HERO Designer saves
writes CHARACTERISTIC on the skill element, so across the 655-character corpus
the template fallback added here fires on exactly zero of 4,434 skill-like
objects. The oracle fixtures stayed green because the change is INERT on them.
Where it fires is documents that OMIT the attribute -- oracle dumps like the
Ravel fixture below, and build docs authored outside this repo (kirby-api's
relational re-emission, the in-app editor), which is the path combat consumes.
This file is therefore the only thing that exercises the fix at all.

Ravel is the owner's own character and ships with this repo as an oracle dump,
so his rolls are HERO Designer's own verdict rather than a re-derivation. His
INT is 23, which is what makes the fix visible: 9 + 23/5 rounds to 14, and the
oracle prints "Deduction 14-".

**Not built on DEX.** Ravel's DEX comes from a power carrying Only In Hero ID,
which this engine does not model, so his DEX-based rolls disagree with the
oracle for an unrelated and separately recorded reason. Everything here is INT-
or GENERAL-based, where the value sits plainly in the characteristics block.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from kirby_cost.io.build_json import build_from_json
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.util.rounder import round_half_up
from tests.corpus import authored_hdc

FIXTURE = Path(__file__).parent / "fixtures" / "authored" / "Ravel.json"

#: Skills Ravel bought that Main6E links to INT, and that his build doc records
#: unambiguously. Each is a single-ITEM CHARACTERISTIC_CHOICE, so the template's
#: default IS the character's choice and nothing else has to be recorded.
#:
#: PROFESSIONAL_SKILL and SCIENCE_SKILL are deliberately absent: their templates
#: offer several ITEMs, HD asks the character which, and the oracle's build dump
#: does not carry the answer — so the engine can only fall back to the template's
#: first, and that disagreement is about the build doc, not about this rule.
INT_BASED = ("DEDUCTION", "CRIMINOLOGY", "FORENSIC_MEDICINE",
             "PARAMEDICS", "COMPUTER_PROGRAMMING", "NAVIGATION")


@pytest.fixture
def ravel(provider):  # noqa: ARG001 — presence of a template is what it gives
    return build_from_json(json.loads(FIXTURE.read_text()))


def _skill(hero, xmlid):
    for skill in hero.skills:
        if skill.xmlid == xmlid:
            return skill
    raise AssertionError(f"Ravel no longer carries {xmlid}")


def test_the_template_names_the_characteristic_a_skill_rolls_against(provider):
    """The linkage the provider used to drop, read straight off the template.

    Every one of these is stated only inside <CHARACTERISTIC_CHOICE>; none of
    them is an attribute of the skill element, which is why reading the element
    alone found nothing.
    """
    assert provider.get_template_data("DEDUCTION").characteristic == "INT"
    assert provider.get_template_data("ACROBATICS").characteristic == "DEX"
    assert provider.get_template_data("KNOWLEDGE_SKILL").characteristic == "GENERAL"


def test_the_linkage_survives_the_load(ravel):
    """A loaded skill knows its characteristic, not just its price."""
    assert _skill(ravel, "DEDUCTION").characteristic_string == "INT"


def test_a_characteristic_based_skill_rolls_off_that_characteristic(ravel):
    """6E1 p57, on Ravel's Deduction; the oracle's own line is "Deduction 14-".

    Spelled out rather than asserted as a bare 14, so a failure says which half
    of the rule broke: the characteristic it read, or the arithmetic on it.
    """
    assert ravel.characteristic_value("INT") == 23.0
    # Standard rounding, via the engine's helper — 23/5 is 4.6, and Python's
    # built-in round() is not what this engine rounds with anywhere.
    assert round_half_up(23.0 / 5.0) == 5
    assert int(_skill(ravel, "DEDUCTION").roll_value) == 9 + 5 == 14


@pytest.mark.parametrize("xmlid", INT_BASED)
def test_every_int_based_skill_ravel_bought_rolls_fourteen(ravel, xmlid):
    """The oracle prints 14- for each of these. One INT, one roll."""
    skill = _skill(ravel, xmlid)
    assert skill.characteristic_string == "INT"
    assert int(skill.roll_value) == 14


def test_a_general_skill_still_rolls_off_the_general_base(ravel):
    """The over-application guard.

    6E1 p57 leaves most Background Skills on the flat general base, and the
    template says which those are by naming GENERAL. Ravel's Knowledge Skill is
    one: its template offers GENERAL or INT, he bought the GENERAL one (it cost
    him 2, not 3), and the oracle prints it at 13- — the general 11 plus the two
    levels he bought, NOT the 16 his INT would give. Fixing the linked case must
    not drag this one along with it.
    """
    ks = _skill(ravel, "KNOWLEDGE_SKILL")
    assert ks.characteristic_string == "GENERAL"
    assert ks.levels == 2
    assert int(ks.roll_value) == 13
    # And with no levels at all, a general skill is the flat 11.
    language = _skill(ravel, "LANGUAGES")
    assert language.characteristic_string == "GENERAL"
    assert language.levels == 0
    assert int(language.roll_value) == 11


def test_the_document_outranks_the_template(provider):
    """A character who states a characteristic keeps it.

    Knowledge Skill's template lists GENERAL first and INT second, and a
    character is entitled to the second. The template must fill the gap, never
    overwrite an answer the document already gave.
    """
    doc = json.loads(FIXTURE.read_text())
    for skill in doc["skills"]:
        if skill["xmlid"] == "KNOWLEDGE_SKILL":
            skill["characteristic"] = "INT"
    hero = build_from_json(doc)
    ks = _skill(hero, "KNOWLEDGE_SKILL")
    assert ks.characteristic_string == "INT"
    assert int(ks.roll_value) == 14 + 2


# ---------------------------------------------------------------------------
# The short circuits: skills that carry a characteristic but do not roll on it.
# ---------------------------------------------------------------------------
#
# 6E1 p62 lists Deduction among the Everyman Skills, so the very skill this
# file uses to prove the linkage is also one a character can hold at the flat
# Everyman roll -- which makes it the right one to prove the linkage is NOT
# consulted there. `roll_value` short-circuits on familiarity and proficiency
# before it ever looks at the characteristic, and nothing in the repo held that
# down: until the alias fix below, every flag in an oracle dump arrived False,
# so these branches were unreachable from any test.


def _ravel_doc():
    return json.loads(FIXTURE.read_text())


def _with_flag(doc, xmlid, **flags):
    for skill in doc["skills"]:
        if skill["xmlid"] == xmlid:
            skill.update(flags)
    return doc


def test_a_familiarity_keeps_its_characteristic_but_does_not_roll_on_it(provider):  # noqa: ARG001
    """A Familiarity is the flat 8-, not nine-plus-a-fifth of anything."""
    hero = build_from_json(
        _with_flag(_ravel_doc(), "DEDUCTION", is_familiarity=True))
    skill = _skill(hero, "DEDUCTION")
    assert skill.is_familiarity
    # The linkage is still THERE -- it is simply not what sets this roll.
    assert skill.characteristic_string == "INT"
    assert int(skill.roll_value) == 8
    assert int(skill.roll_value) != 14


def test_an_everyman_skill_stays_at_eight(provider):  # noqa: ARG001
    """6E1 p62 puts Deduction on the Everyman list; INT 23 must not lift it."""
    hero = build_from_json(_with_flag(
        _ravel_doc(), "DEDUCTION", is_familiarity=True, is_everyman=True))
    skill = _skill(hero, "DEDUCTION")
    assert skill.is_everyman
    assert skill.characteristic_string == "INT"
    assert int(skill.roll_value) == 8


def test_a_proficiency_stays_at_the_flat_proficiency_roll(ravel):
    """Ravel's five Proficiencies, as the oracle prints them: 10-.

    High Society is an Interaction Skill and its template links it to PRE, so
    a linkage-driven roll would be 13. HD prints 10-, because a Proficiency is
    bought as a flat roll and the characteristic never enters. These five are
    what proved the flag aliases in `build_json` mattered: without them the
    fixture's `is_proficiency` was dropped, every one of them loaded as a full
    skill, and this file's own fix pushed them from a wrong 11 to a wrong 13.
    """
    for xmlid in ("HIGH_SOCIETY", "BUREAUCRATICS", "SECURITY_SYSTEMS",
                  "STREETWISE", "INTERROGATION"):
        skill = _skill(ravel, xmlid)
        assert skill.is_proficiency, xmlid
        assert int(skill.roll_value) == 10, xmlid


def test_the_oracle_dumps_flag_spellings_are_accepted(ravel):
    """The aliases themselves, pinned at the seam.

    `Skill.to_build_dict` writes `proficiency`; hd6cli's dump writes
    `is_proficiency`. `build_json` read only the first, so every mode flag in
    an oracle dump silently arrived False -- a skill that HD priced as a
    Proficiency was rebuilt as a full one. Cost-free to fix (High Society is
    2.0 either way) and it is what lets the test above exist at all.
    """
    doc = _ravel_doc()
    stated = {s["xmlid"]: s for s in doc["skills"]}
    assert stated["HIGH_SOCIETY"]["is_proficiency"] is True, \
        "the fixture no longer states the flag this test is about"
    assert "proficiency" not in stated["HIGH_SOCIETY"], \
        "the fixture now uses the canonical spelling; the alias is untested"
    assert _skill(ravel, "HIGH_SOCIETY").is_proficiency
    assert _skill(ravel, "HIGH_SOCIETY").total_cost == 2.0


@pytest.mark.skipif(
    authored_hdc("Ravel") is None,
    reason="KIRBY_COST_AUTHORED unset, or Ravel is not in it",
)
def test_the_characteristic_survives_a_real_hdc_load(provider):  # noqa: ARG001
    """Not only the lossy build-doc path.

    An HD-saved .hdc states CHARACTERISTIC on the skill element, so this load
    exercises the DOCUMENT branch rather than the template fallback -- which is
    the branch the whole 655-character corpus takes, and the reason the parity
    gates say nothing about the fallback. Both must land on INT.
    """
    hero = HDCLoader().load_file(str(authored_hdc("Ravel")))
    deduction = _skill(hero, "DEDUCTION")
    assert deduction._characteristic_from_xml, \
        "an HD-saved .hdc is expected to state CHARACTERISTIC"
    assert deduction.characteristic_string == "INT"
    assert int(deduction.roll_value) == 14
