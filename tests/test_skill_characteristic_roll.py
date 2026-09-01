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

Two paths reach ``roll_value``, and this file exercises both on purpose.

**The canonical path.** ``HDCLoader`` on an HD-saved ``.hdc`` is this
project's canon. Every file HD writes states CHARACTERISTIC on the skill
element, so the document branch runs and the template fallback never fires.
That is the path the 655-character corpus takes and the path combat consumes,
and it is what the tests below assert against by default: Ravel ships with
this repository as ``tests/fixtures/authored/Ravel.hdc``, so there is nothing
to configure and no reason to skip.

**The degraded path**, marked as such wherever it appears below. Documents
that OMIT the attribute — the oracle's JSON dump of Ravel, and build docs
authored outside this repo (kirby-api's relational re-emission, the in-app
editor) — have nothing for the loader to read, and the template fallback added
here is the only thing that gives those skills a characteristic at all. The
parity gates say nothing about it: across the corpus it fires on exactly zero
of 4,434 skill-like objects, so the oracle fixtures stayed green while it was
broken. A handful of tests here therefore build from the dump deliberately.

**Do not confuse the two.** The dump is lossy: it drops CHARACTERISTIC, and it
does not record which ITEM a multi-ITEM skill like PROFESSIONAL_SKILL or
SCIENCE_SKILL was bought as, so those load off the template's first choice.
Asserting engine behaviour against the dump reports differences that are about
the fixture and not about the engine — twice in one evening, before the .hdc
was bundled.

Ravel is the owner's own character. His INT is 23, which is what makes the fix
visible: 9 + 23/5 rounds to 14, and HD prints "Deduction 14-".

**Not built on DEX.** Ravel's DEX comes from a power carrying Only In Hero ID,
which this engine does not model, so his DEX-based rolls disagree with HD for
an unrelated and separately recorded reason. Everything here is INT-, PRE- or
GENERAL-based, where the value sits plainly in the characteristics block.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from kirby_cost.io.build_json import build_from_json
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.util.rounder import round_half_up
from tests.corpus import require_authored_hdc

#: The oracle's JSON dump of Ravel. Used for two things only: the degraded-path
#: tests below, and as the source of HD's own printed rolls (``column2_output``
#: carries the line HD renders, e.g. "Deduction 14-"). It is NOT the character.
DUMP = Path(__file__).parent / "fixtures" / "authored" / "Ravel.json"

#: Skills Ravel bought that Main6E links to INT.
INT_BASED = ("DEDUCTION", "CRIMINOLOGY", "FORENSIC_MEDICINE",
             "PARAMEDICS", "COMPUTER_PROGRAMMING", "NAVIGATION")

#: HD's own printed rolls for Ravel, transcribed from the oracle dump's
#: ``column2_output``. The engine must reproduce every one of these from the
#: .hdc alone. PROFESSIONAL_SKILL and SCIENCE_SKILL are here on purpose: the
#: .hdc records which ITEM he bought and the dump does not, so these two are
#: exactly the cases a dump-based test cannot check.
HD_PRINTED_ROLLS = {
    "PROFESSIONAL_SKILL": 14,
    "SCIENCE_SKILL": 14,
    "HIGH_SOCIETY": 10,
    "BUREAUCRATICS": 10,
    "SECURITY_SYSTEMS": 10,
    "STREETWISE": 10,
    "INTERROGATION": 10,
    "DEDUCTION": 14,
    "ACTING": 13,
    "CHARM": 13,
    "PARAMEDICS": 14,
    "CRIMINOLOGY": 14,
    "FORENSIC_MEDICINE": 14,
    "COMPUTER_PROGRAMMING": 14,
    "NAVIGATION": 14,
    # A GENERAL skill, carried here for completeness: 11 plus his two levels.
    "KNOWLEDGE_SKILL": 13,
}


@pytest.fixture
def ravel(provider):  # noqa: ARG001 — presence of a template is what it gives
    """Ravel, loaded canonically from the bundled .hdc.

    Function-scoped and reloaded per test on purpose: ``load_file`` INSTALLS
    the active hero, and ``roll_value``'s characteristic branch reads it. A
    cached hero would be correct only until some other test loaded another
    character.

    No skip guard, deliberately. The file is tracked, so its absence is a
    deleted fixture, not an unconfigured machine — ``require_authored_hdc``
    raises and the run goes red.
    """
    return HDCLoader().load_file(str(require_authored_hdc("Ravel")))


@pytest.fixture
def ravel_dump(provider):  # noqa: ARG001
    """Ravel rebuilt from the oracle's JSON dump — the DEGRADED path.

    This document omits CHARACTERISTIC on every skill, which is the whole
    reason it is useful: it is the silent document the template fallback
    exists for. It is not a substitute for the .hdc and must never be used to
    judge the engine's numbers.
    """
    return build_from_json(json.loads(DUMP.read_text()))


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


# ---------------------------------------------------------------------------
# The canonical path: a real HD-saved .hdc, loaded through HDCLoader.
# ---------------------------------------------------------------------------


def test_ravel_reproduces_every_roll_hero_designer_printed(ravel):
    """The whole character at once, against HD's own verdict.

    Each expected value is the roll HD rendered into its own output for this
    build (``column2_output`` in the oracle dump, e.g. "Deduction 14-"), and
    the engine has to arrive at it from the .hdc alone. This is the test that
    catches a lossy fixture pretending to be a regression: five Proficiencies
    and the two multi-ITEM skills are all in here, and all seven are cases the
    dump cannot state.
    """
    mismatched = {}
    for xmlid, printed in HD_PRINTED_ROLLS.items():
        got = int(_skill(ravel, xmlid).roll_value)
        if got != printed:
            mismatched[xmlid] = (got, printed)
    assert not mismatched, f"engine vs HD's printed rolls: {mismatched}"


def test_the_transcribed_rolls_are_still_the_ones_hero_designer_printed():
    """The provenance check on the table above.

    Takes no hero: it reads HD's rendered output and the transcription, and
    never loads a character.

    ``HD_PRINTED_ROLLS`` is transcribed, and a transcription can rot. This
    re-reads the rolls out of HD's own rendered lines and insists they still
    agree, so the previous test cannot quietly become a test of a typo.
    """
    printed_by_xmlid = {}
    for entry in json.loads(DUMP.read_text())["skills"]:
        match = re.search(r"(\d+)-\s*$", entry.get("column2_output") or "")
        if match:
            printed_by_xmlid.setdefault(entry["xmlid"], int(match.group(1)))
    for xmlid, expected in HD_PRINTED_ROLLS.items():
        assert printed_by_xmlid.get(xmlid) == expected, xmlid
    # And nothing HD printed a roll for is left out of the table. Ravel's
    # other two skills -- LANGUAGES and SKILL_LEVELS -- are absent because HD
    # renders no roll for either, not because they were skipped.
    assert set(printed_by_xmlid) == set(HD_PRINTED_ROLLS), \
        "a skill HD prints a roll for is no longer covered by HD_PRINTED_ROLLS"


def test_an_hd_saved_file_states_the_characteristic_on_the_element(ravel):
    """The canonical branch is the DOCUMENT branch, not the fallback.

    Worth pinning: if HD ever stopped writing CHARACTERISTIC, every canonical
    assertion here would start silently running through the template fallback
    instead, and this file would stop testing what it says it tests.
    """
    deduction = _skill(ravel, "DEDUCTION")
    assert deduction._characteristic_from_xml, \
        "an HD-saved .hdc is expected to state CHARACTERISTIC"
    assert deduction.characteristic_string == "INT"


def test_a_characteristic_based_skill_rolls_off_that_characteristic(ravel):
    """6E1 p57, on Ravel's Deduction; HD's own line is "Deduction 14-".

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
    """HD prints 14- for each of these. One INT, one roll."""
    skill = _skill(ravel, xmlid)
    assert skill.characteristic_string == "INT"
    assert int(skill.roll_value) == 14


def test_a_general_skill_still_rolls_off_the_general_base(ravel):
    """The over-application guard.

    6E1 p57 leaves most Background Skills on the flat general base, and the
    template says which those are by naming GENERAL. Ravel's Knowledge Skill is
    one: its template offers GENERAL or INT, he bought the GENERAL one (it cost
    him 2, not 3), and HD prints it at 13- — the general 11 plus the two levels
    he bought, NOT the 16 his INT would give. Fixing the linked case must not
    drag this one along with it.
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


def test_a_proficiency_stays_at_the_flat_proficiency_roll(ravel):
    """Ravel's five Proficiencies, as HD prints them: 10-.

    High Society is an Interaction Skill and its template links it to PRE, so
    a linkage-driven roll would be 13. HD prints 10-, because a Proficiency is
    bought as a flat roll and the characteristic never enters: ``roll_value``
    short-circuits on the flag before it ever looks at the characteristic.
    """
    for xmlid in ("HIGH_SOCIETY", "BUREAUCRATICS", "SECURITY_SYSTEMS",
                  "STREETWISE", "INTERROGATION"):
        skill = _skill(ravel, xmlid)
        assert skill.is_proficiency, xmlid
        assert int(skill.roll_value) == 10, xmlid


def test_a_multi_item_skill_keeps_the_item_the_character_bought(ravel):
    """The two skills the dump cannot describe, and why the .hdc is canon.

    PROFESSIONAL_SKILL and SCIENCE_SKILL each offer several ITEMs; HD asks the
    character which, writes the answer into the .hdc, and does not carry it in
    the JSON dump. Loaded canonically both land on INT and both roll 14, which
    is what HD printed. Loaded from the dump the engine can only take the
    template's first ITEM, and a test that judged the engine there was judging
    the fixture.
    """
    for xmlid in ("PROFESSIONAL_SKILL", "SCIENCE_SKILL"):
        skill = _skill(ravel, xmlid)
        assert skill.characteristic_string == "INT", xmlid
        assert int(skill.roll_value) == 14, xmlid


# ---------------------------------------------------------------------------
# The degraded path, ON PURPOSE: documents that omit CHARACTERISTIC.
#
# Everything below builds from the oracle's JSON dump or a hand-edited copy of
# it, because that is the only shape in which the template fallback fires at
# all. These are the tests this branch was written for. They are NOT a second
# opinion on the engine's numbers; where a number here differs from the
# canonical path above, the dump is what is wrong.
# ---------------------------------------------------------------------------


def _ravel_doc():
    return json.loads(DUMP.read_text())


def test_the_dump_states_no_characteristic_at_all(ravel_dump):
    """The premise of every degraded-path test here, pinned.

    If the dump ever started carrying CHARACTERISTIC, the fallback would stop
    firing and these tests would go on passing while testing nothing.
    """
    stated = [s for s in _ravel_doc()["skills"] if s.get("characteristic")]
    assert not stated, \
        "the dump now states CHARACTERISTIC; the template fallback is untested"
    # ...and the fallback supplied it anyway.
    assert _skill(ravel_dump, "DEDUCTION").characteristic_string == "INT"


def test_the_fallback_gives_a_silent_document_the_right_roll(ravel_dump):
    """A build doc that names no characteristic still rolls 14 off INT 23.

    This is the path kirby-api's relational re-emission and the in-app editor
    take, and the one combat consumes.
    """
    assert ravel_dump.characteristic_value("INT") == 23.0
    assert int(_skill(ravel_dump, "DEDUCTION").roll_value) == 14


def test_the_document_outranks_the_template(provider):  # noqa: ARG001
    """A character who states a characteristic keeps it.

    Knowledge Skill's template lists GENERAL first and INT second, and a
    character is entitled to the second. The template must fill the gap, never
    overwrite an answer the document already gave.
    """
    doc = _ravel_doc()
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
# consulted there. Ravel does not actually hold Deduction that way, so these
# flip the flags on a copy of his build doc; the degraded path is incidental
# here, and what is under test is `roll_value`'s ordering.


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


def test_the_oracle_dumps_flag_spellings_are_accepted(ravel_dump):
    """The aliases themselves, pinned at the seam.

    `Skill.to_build_dict` writes `proficiency`; hd6cli's dump writes
    `is_proficiency`. `build_json` read only the first, so every mode flag in
    an oracle dump silently arrived False -- a skill that HD priced as a
    Proficiency was rebuilt as a full one. Cost-free to fix (High Society is
    2.0 either way), and it is what keeps the dump usable as a build doc at
    all.
    """
    stated = {s["xmlid"]: s for s in _ravel_doc()["skills"]}
    assert stated["HIGH_SOCIETY"]["is_proficiency"] is True, \
        "the fixture no longer states the flag this test is about"
    assert "proficiency" not in stated["HIGH_SOCIETY"], \
        "the fixture now uses the canonical spelling; the alias is untested"
    assert _skill(ravel_dump, "HIGH_SOCIETY").is_proficiency
    assert _skill(ravel_dump, "HIGH_SOCIETY").total_cost == 2.0
