"""Everything the document said, the export says back.

The oracle suite proves the engine COSTS a character the way HERO Designer
does. It says nothing about whether the character survives being written out
again, because it never writes one — and a character that reloads short of
what it was is wrong in a way no cost comparison can see.

Measured 2026-08-18, before any of this was fixed: of 794 corpus characters,
485 came back saying something different from what was read. A CUSTOMPOWER
lost all twelve attributes that define what it DOES; a Force Wall lost the
PD/ED/MD/POWD split HD costs it by; every character with a campaign
``<RULES>`` block lost the block entire. None of it failed loudly. The file
opened, and the character was quietly someone else.

So this asserts the whole property at once, over every character available:
**every element and every attribute the source stated is stated again by the
export, with the same value.** Not a sample of them, and not the ones somebody
remembered to list.

The ledger works like ``oracle_known_residuals.json``: shrink-only, with a
staleness ratchet. When a class starts round-tripping, its entry comes out in
the same commit — ``test_export_ledger_is_not_stale`` fails until it does, and
that failure is a free win, not a regression.

It has two lists, and the difference between them is the whole discipline:

``gaps``
    Defects. Known, not yet fixed, and each one a character that comes back
    saying less than it said. This list is meant to reach zero, and it has.

``matches_hd``
    Diffs HERO DESIGNER ITSELF produces on a re-save, so reproducing them is
    fidelity rather than damage. Each entry states the Java that does it,
    because "HD does this too" is exactly the excuse that would hide a real
    defect if it were ever accepted without one. Two entries, both normalising:
    HD trims TEXT (``textOutput = check.trim()``) and HD re-resolves an
    option's cost onto BASECOST after restoring it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.export_survey import FIXTURES, ledger, no_corpus, survey as run_survey

LEDGER_PATH = FIXTURES / "export_known_gaps.json"

pytestmark = no_corpus


@pytest.fixture(scope="module")
def survey():
    return run_survey()


def test_export_states_everything_the_source_stated(survey):
    """No character may come back saying less than it said."""
    gaps, clean, total = survey
    known = ledger(LEDGER_PATH)
    new = {k: v for k, v in gaps.items() if k not in known}
    if new:
        lines = [f"{len(new)} export gaps not in the ledger "
                 f"({clean}/{total} characters round-trip clean):"]
        for key, hits in sorted(new.items(), key=lambda kv: -len(kv[1]))[:20]:
            lines.append(f"  {key}  ({len(hits)} occurrences)")
            lines.append(f"      e.g. {hits[0]}")
        pytest.fail("\n".join(lines))


def test_export_ledger_is_not_stale(survey):
    """A ledger entry that no longer reproduces is a free win — delete it."""
    gaps, _, _ = survey
    fixed = sorted(ledger(LEDGER_PATH) - set(gaps))
    if fixed:
        pytest.fail(
            "ledger entries that no longer reproduce — delete them:\n  "
            + "\n  ".join(fixed))
