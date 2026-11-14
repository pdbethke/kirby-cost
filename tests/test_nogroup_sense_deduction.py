"""A NOGROUP sense DOES take the sense-group deduction. Three wrong answers first.

This file is kept as a record of how a single number resisted four explanations.
A corpus villain's "Lifesense" DETECT: base 10 + DISCRIMINATORY 5 + RANGE 5 +
MAKEASENSE 2 + TARGETINGSENSE 10 = 32, against a deduction of 1 for
ENHANCEDPERCEPTION, which the group is deemed to provide.

**1. "NOGROUP means no group, so never deduct."** Disproved by measurement:
suppressing the deduction for NOGROUP took the corpus from 4 failures to 14.
NOGROUP is a real group — `SenseGroup.clear()` synthesises it alongside
UNUSUALGROUP and `getAllGroups()` returns both — and it holds senses that fit no
normal group, such as Lifesense.

**2. "DETECT needs Java's getDetectDisplay gate."** `Sense.builtInSenseAdders`
does gate a DETECT on the adder naming that specific Detect. Real, but not this
bug: `getTotalCost`'s deduction reads the `senseAdders` FIELD against
`getGroup().getSenseAdders()` and never touches `builtInSenseAdders`. A strict
xfail sat here for months waiting for a port that was not required.

**3. "No TEMPLATE attribute, so no sense groups are registered."** This one
passed the corpus test — that character is the only one of 12 identically shaped
Detects whose file declares no template, and the only one the oracle did not
deduct for — and it shipped. It was wrong.

**4. The oracle was broken.** The headless HD fork could not resolve any
`builtIn.` template name, so Main6E loaded without the parent chain that
registers the sense groups. Its 32 was never HD's answer; it was the
answer of an HD that had failed to finish loading its template. Fixed in
the comparison harness on 2026-08-17, the oracle says **31** — the engine's
original, unmodified answer, before any of (1), (2) or (3) were attempted.

Three of the four hypotheses were tested against the corpus and one of them
even passed. None of that could distinguish a rule from an instrument fault,
because every reading came from the same faulty instrument. What settled it was
re-running the oracle after fixing the oracle.
"""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.own_copy import own_copy


def _adder(xmlid, adder_id, base, alias):
    return (f'<ADDER XMLID="{xmlid}" ID="{adder_id}" BASECOST="{base}" LEVELS="0" '
            f'ALIAS="{alias}" POSITION="-1" MULTIPLIER="1.0" SHOWALIAS="Yes" '
            f'PRIVATE="No" REQUIRED="No" INCLUDEINBASE="No" DISPLAYINSTRING="Yes" '
            f'GROUP="No" SELECTED="YES" />')


# The same shape as that Detect, on a temporary copy of PowerLad.
_LIFESENSE = (
    '<POWER XMLID="DETECT" ID="9000000000120" BASECOST="10.0" LEVELS="0" ALIAS="Detect Life" '
    'POSITION="99" MULTIPLIER="1.0" OPTION="LARGECLASS" OPTIONID="LARGECLASS" '
    'OPTION_ALIAS="A Large Class Of Things" NAME="Lifesense" QUANTITY="1" '
    'AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes" GROUP="NOGROUP" ACTIVE="Yes">'
    + _adder("DISCRIMINATORY", 9000000000121, 5.0, "Discriminatory")
    + _adder("RANGE", 9000000000122, 5.0, "Range")
    + _adder("MAKEASENSE", 9000000000123, 2.0, "Make It A Sense")
    + _adder("TARGETINGSENSE", 9000000000124, 10.0, "Targeting")
    + "<PROVIDES>ENHANCEDPERCEPTION</PROVIDES>"
    + "</POWER>")


# The group "provides" Enhanced Perception once the character has bought it for
# every sense, and only for a Detect loaded AFTER that purchase (the SenseGroup
# cache the loader mirrors), so it goes in the file first.
_ENHANCED_PERCEPTION = (
    '<POWER XMLID="ENHANCEDPERCEPTION" ID="9000000000125" BASECOST="0.0" LEVELS="2" '
    'ALIAS="Enhanced Perception" POSITION="98" MULTIPLIER="1.0" OPTION="ALL" '
    'OPTIONID="ALL" OPTION_ALIAS="all Sense Groups" NAME="Probe Perception" />')


def test_nogroup_sense_takes_the_group_deduction(tmp_path):
    hero = HDCLoader().load_file(own_copy(
        tmp_path, section_xml=[("POWERS", _ENHANCED_PERCEPTION), ("POWERS", _LIFESENSE)]))

    lifesense = next(
        (p for p in hero.powers
         if p.xmlid == "DETECT" and getattr(p, "name", None) == "Lifesense"),
        None,
    )
    assert lifesense is not None, "Lifesense DETECT not loaded"
    assert lifesense.group_id == "NOGROUP", "fixture must exercise the NOGROUP path"

    adder_sum = sum(a.total_cost for a in lifesense._assigned_adders)
    expected = lifesense._base_cost + adder_sum - 1.0   # the group deduction

    assert lifesense.total_cost == expected, (
        f"Lifesense cost {lifesense.total_cost}, expected {expected} "
        f"(= base {lifesense._base_cost} + adders {adder_sum} - 1 for the "
        "ENHANCEDPERCEPTION the group provides). NOGROUP is a real group and "
        "deducts like any other."
    )
    assert lifesense.total_cost == 31.0
