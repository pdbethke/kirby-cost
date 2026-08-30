"""Every cost on the validation sink, against HD's own dump -- with a shrink-only ledger.

The 655-fixture corpus is HD-WRITTEN, so a stated modifier BASECOST there always
equals what HD would recompute -- which hid a real divergence: HD restores a
modifier's stated BASECOST and then OVERWRITES it when the option restores
(GenericObject.java:3665 reads BASECOST, :3747 reads OPTIONID, and
setSelectedOption() ends with setBaseCost(option.getBaseCost())), where this
engine lets the stated value win (`_base_cost_from_xml`). Proved by mutation:
setting Blast AOE's AOE BASECOST to 9.75 moved HD's answer not at all
(2026-08-30). The validation sink is hand-written, so its lying BASECOSTs
expose the divergence the corpus cannot.

``validation_sink_cost_gaps.json`` is SHRINK-ONLY, the same standing as the
included ledgers: every disagreeing (object, field) is listed with a curated
reason; a new disagreement fails the suite; one that starts agreeing must be
removed. Regenerate the fixture with the commands in its ``_comment``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "authored" / "ValidationSink.json"
LEDGER_PATH = Path(__file__).parent / "fixtures" / "validation_sink_cost_gaps.json"

#: oracle field -> engine attribute (real_cost is PRE-LIST, as in
#: tests/test_authored_characters.py -- the oracle dumps getRealCostPreList()).
COST_FIELDS = {"total_cost": "total_cost", "active_cost": "active_cost",
               "real_cost": "real_cost_pre_list"}


def _fixture_objects() -> list[dict]:
    out: list[dict] = []

    def walk(o):
        if isinstance(o, dict):
            if "id" in o:
                out.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(json.loads(FIXTURE.read_text()))
    return out


def _ledger() -> dict[str, str]:
    if not LEDGER_PATH.exists():
        return {}
    return json.loads(LEDGER_PATH.read_text()).get("gaps", {})


def _survey() -> dict[str, str]:
    from tests.matrix_support import object_index, sink_hero
    index = object_index(sink_hero())
    wrong: dict[str, str] = {}
    for o in _fixture_objects():
        e = index.get(str(o["id"]))
        if e is None:
            continue
        for field, attr in COST_FIELDS.items():
            ev = getattr(e, attr, None)
            if ev is None:
                continue
            if abs((o.get(field) or 0) - ev) > 0.01:
                wrong[f"{o['id']}:{field}"] = (
                    f"HD {o.get(field)} engine {ev} ({o['xmlid']} {o.get('name', '')!r})")
    return wrong


@pytest.fixture(scope="module")
def survey():
    return _survey()


def test_the_cost_survey_is_substantial():
    assert len(_fixture_objects()) > 60


def test_no_new_cost_disagreement_with_hero_designer(survey):
    new = {k: v for k, v in survey.items() if k not in _ledger()}
    if new:
        lines = [f"{len(new)} sink costs disagree with HD and are not in the ledger:"]
        lines += [f"  {k}\n      {v}" for k, v in sorted(new.items())]
        pytest.fail("\n".join(lines))


def test_the_cost_ledger_is_not_stale(survey):
    fixed = sorted(set(_ledger()) - set(survey))
    if fixed:
        pytest.fail(f"{len(fixed)} cost-ledger entries now agree with HD. Remove them from "
                    f"{LEDGER_PATH.name} in the commit that fixed them:\n  " + "\n  ".join(fixed))
