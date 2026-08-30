"""Every cell of HD's applicability matrix, against the engine's included().

``included_known_gaps.json`` is a SHRINK-ONLY ledger, the same standing as
``display_known_gaps.json``: a cell listed there is a known divergence with a
reason; a failure not in the ledger fails the suite; an entry that starts
passing must be removed in the commit that fixed it.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.matrix_support import blank_hero_context, cell_key, cells, template_modifier, template_power

LEDGER_PATH = Path(__file__).parent / "fixtures" / "included_known_gaps.json"


def _ledger() -> dict[str, str]:
    if not LEDGER_PATH.exists():
        return {}
    return json.loads(LEDGER_PATH.read_text()).get("gaps", {})


def _verdict(cell: dict) -> tuple[bool, str]:
    mod = template_modifier(cell["modifier"])
    power = template_power(cell["power"])
    reason = mod.included(power) or ""
    return (reason.strip() == ""), reason


def _survey() -> dict[str, str]:
    """{cell key: what went wrong} for every cell the engine disagrees on."""
    blank_hero_context()
    wrong: dict[str, str] = {}
    for c in cells():
        try:
            allowed, reason = _verdict(c)
        except FileNotFoundError:
            # "No HERO Designer template configured" is not a verdict; let it
            # reach conftest's hook, which turns it into a skip (CI has no
            # template). Swallowing it here counted 7,924 phantom gaps.
            raise
        except Exception as e:  # noqa: BLE001 -- a crash is a gap too
            wrong[cell_key(c["modifier"], c["power"])] = f"raised {type(e).__name__}: {e}"
            continue
        if allowed != c["allowed"] or reason != c["reason"]:
            wrong[cell_key(c["modifier"], c["power"])] = (
                f"engine allowed={allowed} {reason!r}  HD allowed={c['allowed']} {c['reason']!r}")
    return wrong


@pytest.fixture(scope="module")
def survey():
    return _survey()


def test_the_matrix_is_substantial():
    assert len(cells()) > 5000


def test_no_new_disagreement_with_hero_designer(survey):
    """No cell may disagree with HD unless the ledger says why."""
    new = {k: v for k, v in survey.items() if k not in _ledger()}
    if new:
        lines = [f"{len(new)} cells disagree with HD and are not in the ledger "
                 f"({len(cells()) - len(survey):,}/{len(cells()):,} exact):"]
        for k, v in sorted(new.items())[:25]:
            lines.append(f"  {k}\n      {v}")
        pytest.fail("\n".join(lines))


def test_the_ledger_is_not_stale(survey):
    """A ledger entry that now agrees with HD is a free win -- delete it."""
    fixed = sorted(set(_ledger()) - set(survey))
    if fixed:
        pytest.fail(
            f"{len(fixed)} ledger entries now agree with HD. Remove them from "
            f"{LEDGER_PATH.name} in the commit that fixed them:\n  " + "\n  ".join(fixed))
