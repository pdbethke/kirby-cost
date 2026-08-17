"""A NOGROUP sense DOES take the sense-group deduction. Three wrong answers first.

This file is kept as a record of how a single number resisted four explanations.
UNDEAD_LICH's "Lifesense" DETECT: base 10 + DISCRIMINATORY 5 + RANGE 5 +
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
passed the corpus test — the LICH is the only one of 12 identically shaped
Detects whose file declares no template, and the only one the oracle did not
deduct for — and it shipped. It was wrong.

**4. The oracle was broken.** The headless HD fork could not resolve any
`builtIn.` template name, so Main6E loaded without the parent chain that
registers the sense groups. The LICH's 32 was never HD's answer; it was the
answer of an HD that had failed to finish loading its template. Fixed in
the HD oracle harness on 2026-08-17, the oracle says **31** — the engine's
original, unmodified answer, before any of (1), (2) or (3) were attempted.

Three of the four hypotheses were tested against the corpus and one of them
even passed. None of that could distinguish a rule from an instrument fault,
because every reading came from the same faulty instrument. What settled it was
re-running the oracle after fixing the oracle.
"""
import glob
import json
import pathlib

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

FIXTURE = glob.glob("tests/fixtures/oracle/*UNDEAD_LICH*.json")


@pytest.mark.skipif(not FIXTURE, reason="UNDEAD_LICH oracle fixture not present")
def test_nogroup_sense_takes_the_group_deduction():
    fx = json.load(open(FIXTURE[0]))
    if not pathlib.Path(fx["hdc_path"]).exists():
        pytest.skip("HDC source not present on this machine")

    hero = HDCLoader().load_file(fx["hdc_path"])

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
