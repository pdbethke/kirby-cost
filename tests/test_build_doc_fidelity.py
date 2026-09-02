"""Everything the document said, the JSON door says back.

The chain graded here is the whole one:

    .hdc  ->  hero  ->  build doc  ->  hero  ->  .hdc

and the result is compared attribute-for-attribute against the file it started
from, by the same survey ``test_export_fidelity`` uses. The two differ only in
the middle hop, which is the point: when both fail, the writer lost the field;
when only this one fails, the build doc did.

Why this did not exist. The build doc had exactly one gate,
``test_ose_json_roundtrip_is_lossless``, and despite its name all it compared
was the summed ``real_cost``:

    again = build_from_json(to_build_json(ref))
    assert round(_total(again)) == round(_total(ref))

Every field the doc has been caught dropping — TEXT, NOTES, a power's NAME, a
modifier's ALIAS ("Only With Tail", the descriptor that makes a limitation a
limitation), AFFECTS_PRIMARY / AFFECTS_TOTAL — is COST-NEUTRAL. A cost gate
could not have seen one of them, and five were found one at a time, by hand,
after each had already reached the database. Meanwhile the .hdc path had the
attribute-level property the whole time.

The underlying defect is duplication, not oversight: ``get_save_xml`` writes
from the DECLARED schema (``XML_ATTRS`` / ``xml_schema()``), so an attribute
added to a class is written automatically, while ``to_build_dict`` re-derives
the same knowledge as a hand-written list of ``if getattr(...)`` lines, and
the doc's input side re-derives it a third time in ``_ATTR`` / ``_BOOL`` /
``_TYPED_ATTR``. Each new field is one omission away from being dropped
silently. This gate makes that omission loud; emitting from the schema is what
stops it happening.
"""
from __future__ import annotations

import pytest

from kirby_cost.io.formats import load_build
from tests.export_survey import FIXTURES, ledger, no_corpus, survey as run_survey

LEDGER_PATH = FIXTURES / "json_known_gaps.json"

pytestmark = no_corpus


def _through_the_json_door(hero):
    """The whole chain: .hdc -> hero -> json -> hero -> .hdc."""
    return load_build(hero.export(format="json"), format="json")


@pytest.fixture(scope="module")
def survey():
    return run_survey(_through_the_json_door)


def test_the_build_doc_states_everything_the_source_stated(survey):
    """No character may come back from the doc saying less than it said."""
    gaps, clean, total = survey
    known = ledger(LEDGER_PATH)
    new = {k: v for k, v in gaps.items() if k not in known}
    if new:
        lines = [f"{len(new)} build-doc gaps not in the ledger "
                 f"({clean}/{total} characters round-trip clean):"]
        for key, hits in sorted(new.items(), key=lambda kv: -len(kv[1]))[:20]:
            lines.append(f"  {key}  ({len(hits)} occurrences)")
            lines.append(f"      e.g. {hits[0]}")
        pytest.fail("\n".join(lines))


def test_build_doc_ledger_is_not_stale(survey):
    """A ledger entry that no longer reproduces is a free win — delete it."""
    gaps, _, _ = survey
    fixed = sorted(ledger(LEDGER_PATH) - set(gaps))
    if fixed:
        pytest.fail(
            "ledger entries that no longer reproduce — delete them:\n  "
            + "\n  ".join(fixed))
