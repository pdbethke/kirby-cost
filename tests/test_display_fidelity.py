"""What HD prints, this engine prints.

The oracle suite proves the engine COSTS a character the way HERO Designer
does. The export suite proves the character survives being written back out.
Neither says anything about what a character SHEET reads like, and until
2026-08-19 nothing could: the display layer here is a set of deliberate stubs
(``GenericObject.modifier_string`` returns "" and says so), and the oracle
dumped costs only, so there was nothing to check them against.

The oracle dumps ``column2_output``, ``modifier_string`` and ``adder_string``
now, keyed by HD's element id, and the fixtures carry them. So this compares,
object by object, over every character available.

Measured 2026-08-19, before any of it was ported — 655 characters, 30,564
objects:

    column2_output    10.1% exact     Characteristic is 14,217 of the failures
    modifier_string   79.9% exact     the stub is only wrong when there is
                                      something to say, which is 20% of the time
    adder_string      87.8% exact     Disadvantage is 2,686 of the 3,187 wrong

``adder_string`` matters most in what it reveals: those are not stubs. That
code is ported and subtly WRONG — it renders "+9 PD x0, Fill In" where HD
writes "+9 PD, Fill In", and "x8 Noncombat x8" for "x8 Noncombat". A stub is
honest about knowing nothing. This was confidently producing a duplicated
multiplier, and no test could see it.

The ledger is the same shrink-only instrument the export gate uses, keyed by
FIELD and CLASS, because these are class defects: one Characteristic formatting
rule accounts for half of everything wrong with column2_output. An entry is a
known gap, never an acceptable difference.

**A ported string is exact or it is not ported.** There is no partial credit
here and deliberately so — "close enough" display text is how a sheet ends up
subtly wrong everywhere instead of obviously wrong in one place.
"""
from __future__ import annotations

import collections
import glob
import json
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "oracle"
LEDGER_PATH = Path(__file__).parent / "fixtures" / "display_known_gaps.json"

FIELDS = ("column2_output", "modifier_string", "adder_string")
SECTIONS = ("characteristics", "powers", "skills", "perks", "talents",
            "complications", "martial_arts", "equipment")

pytestmark = pytest.mark.skipif(
    not list(FIXTURE_DIR.glob("*.json")),
    reason="no oracle fixtures generated (see kirby-utils)",
)


def _ledger() -> set[str]:
    if not LEDGER_PATH.exists():
        return set()
    return set(json.loads(LEDGER_PATH.read_text()).get("gaps", []))


def _oracle_index(fixture: dict) -> dict:
    """{element id: {field: what HD prints}}, children included."""
    out: dict = {}

    def walk(objects):
        for obj in objects or ():
            if obj.get("id") is not None:
                out[str(obj["id"])] = {f: obj.get(f) for f in FIELDS}
            walk(obj.get("sub_powers"))
            walk(obj.get("modifiers"))
            walk(obj.get("adders"))

    for section in SECTIONS:
        walk(fixture.get(section))
    return out


def _engine_index(hero) -> dict:
    """{element id: object}, by the same id, children included."""
    out: dict = {}

    def walk(objects):
        for obj in objects or ():
            ident = getattr(obj, "_id", None)
            if ident is not None:
                out[str(ident)] = obj
            walk(getattr(obj, "powers", None))
            walk(getattr(obj, "_assigned_modifiers", None))
            walk(getattr(obj, "_assigned_adders", None))

    for section in SECTIONS:
        walk(getattr(hero, section, None))
    return out


def _survey() -> tuple[dict, collections.Counter, int]:
    """Compare every object. Returns (gaps, tallies, objects compared)."""
    loader = HDCLoader()
    gaps: dict = collections.defaultdict(list)
    tally: collections.Counter = collections.Counter()
    compared = 0

    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture = json.loads(path.read_text())
        hdc = fixture.get("hdc_path", "")
        if not hdc or not Path(hdc).exists():
            continue
        try:
            hero = loader.load_file(hdc)
        except Exception:  # noqa: BLE001 — a load failure is the oracle suite's problem
            continue

        engine = _engine_index(hero)
        for ident, wanted in _oracle_index(fixture).items():
            obj = engine.get(ident)
            if obj is None:
                continue
            cls = type(obj).__name__
            for field, hd in wanted.items():
                if hd is None:
                    continue
                compared += 1
                key = f"{field}|{cls}"
                try:
                    mine = getattr(obj, field, None)
                except Exception as exc:  # noqa: BLE001
                    tally["raised"] += 1
                    gaps[key].append(f"{path.stem}: raised {type(exc).__name__}")
                    continue
                if mine is not None and str(mine) == hd:
                    tally["exact"] += 1
                    continue
                tally["wrong"] += 1
                if len(gaps[key]) < 4:
                    gaps[key].append(
                        f"{path.stem}: engine {str(mine)[:70]!r} != HD {hd[:70]!r}")
                else:
                    gaps[key].append("")
    return gaps, tally, compared


@pytest.fixture(scope="module")
def survey():
    return _survey()


def test_display_matches_hero_designer(survey):
    """No class may start printing something HD does not."""
    gaps, tally, compared = survey
    new = {k: v for k, v in gaps.items() if k not in _ledger()}
    if new:
        lines = [f"{len(new)} display gaps not in the ledger "
                 f"({tally['exact']:,}/{compared:,} strings exact):"]
        for key, hits in sorted(new.items(), key=lambda kv: -len(kv[1]))[:20]:
            lines.append(f"  {key}  ({len(hits)} objects)")
            first = next((h for h in hits if h), "")
            if first:
                lines.append(f"      e.g. {first}")
        pytest.fail("\n".join(lines))


def test_display_ledger_is_not_stale(survey):
    """A ledger entry that no longer reproduces is a free win — delete it."""
    gaps, _, _ = survey
    fixed = sorted(_ledger() - set(gaps))
    if fixed:
        pytest.fail(
            f"{len(fixed)} ledger entries no longer reproduce. Remove them from "
            f"{LEDGER_PATH.name} in the commit that fixed them:\n  "
            + "\n  ".join(fixed))
