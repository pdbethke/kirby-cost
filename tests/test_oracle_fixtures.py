"""Oracle comparison tests using pre-generated fixtures.

These fixtures are immutable — generated once from the Java HD6 CLI.
Tests load each fixture, run the Python HDCLoader, and compare costs.
"""
import json
import pytest
from pathlib import Path

from kirby_cost.io.hdc_loader import HDCLoader

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "oracle"
FW_CLASSES = {"Multipower", "VariablePowerPool", "ElementalControl", "List"}
FW_XMLIDS = {"MULTIPOWER", "VPP", "ELEMENTALCONTROL"}

_RESIDUALS_PATH = Path(__file__).parent / "fixtures" / "oracle_known_residuals.json"
# Loud failure if the ledger is missing — never silently widen or narrow the gate.
_residuals_doc = json.loads(_RESIDUALS_PATH.read_text())
KNOWN_TOTALS_RESIDUALS: set[str] = set(_residuals_doc.get("residuals", {}).keys())


def _fixture_files():
    """Yield all oracle fixture JSON files."""
    if not FIXTURE_DIR.exists():
        return []
    return sorted(FIXTURE_DIR.glob("*.json"))


def _filter_oracle(oracle_list):
    return [j for j in oracle_list if j.get("class") not in FW_CLASSES]


def _filter_python(py_list):
    return [
        p for p in py_list
        if p.xmlid not in FW_XMLIDS
        and not (
            p.xmlid == "GENERIC_OBJECT"
            and p.levels == 0
            and p.level_cost == 0.0
        )
    ]


@pytest.mark.parametrize("fixture_path", _fixture_files(), ids=lambda p: p.stem)
def test_oracle_match(fixture_path):
    """Every object's cost must match the frozen Java oracle."""
    fixture = json.loads(fixture_path.read_text())
    hdc_path = fixture["hdc_path"]

    if not Path(hdc_path).exists():
        pytest.skip(f"HDC file missing: {hdc_path}")

    hero = HDCLoader().load_file(hdc_path)

    mismatches = []
    for section, hero_list in [
        ("powers", hero.powers),
        ("skills", hero.skills),
        ("perks", hero.perks),
        ("talents", hero.talents),
        ("martial_arts", hero.martial_arts),
    ]:
        oracle_list = _filter_oracle(fixture.get(section, []))
        py_list = _filter_python(hero_list)

        for i, oracle_obj in enumerate(oracle_list):
            if i >= len(py_list):
                break
            py_obj = py_list[i]
            for field in ("total_cost", "active_cost", "real_cost"):
                py_val = (
                    py_obj.total_cost if field == "total_cost"
                    else py_obj.active_cost if field == "active_cost"
                    else py_obj.real_cost_pre_list
                )
                if abs(py_val - oracle_obj[field]) > 0.01:
                    mismatches.append(
                        f"{section}[{i}] {py_obj.xmlid} "
                        f"{field}: py={py_val} oracle={oracle_obj[field]}"
                    )
                    break

    # Character-level totals — the assertion class that catches ANY
    # silently dropped section (this bug class shipped once: MARTIALARTS).
    name = fixture_path.stem
    if name not in KNOWN_TOTALS_RESIDUALS:
        if "total_points" in fixture and abs(hero.total_points - fixture["total_points"]) > 0.01:
            mismatches.append(
                f"total_points: python={hero.total_points} java={fixture['total_points']}"
            )
        if "available_points" in fixture and abs(hero.available_points - fixture["available_points"]) > 0.01:
            mismatches.append(
                f"available_points: python={hero.available_points} java={fixture['available_points']}"
            )
    if "unparsed_sections" in fixture:
        # SUBSET, not equality. The two lists are not the same fact: each names
        # the sections THAT engine did not parse. The Java CLI does not emit
        # EQUIPMENT, so it reports it unparsed for all 655 characters; the
        # Python loader does parse it, so it reports nothing. Python covering
        # MORE of the file than the reference CLI is progress, not divergence.
        #
        # The guard's purpose survives intact. It exists to catch a section
        # silently dropped by the loader — that shipped once, with MARTIALARTS
        # — and a dropped section makes Python's unparsed set GROW, which
        # breaks the subset and still fails loudly.
        #
        # These were compared for equality until 2026-08-17, and passed only
        # because the committed fixtures predated the CLI emitting the field at
        # all and recorded a blanket []. Regenerating the corpus surfaced it on
        # every character at once.
        extra = sorted(set(hero.unparsed_sections) - set(fixture["unparsed_sections"]))
        if extra:
            mismatches.append(
                f"unparsed_sections: python did not parse {extra}, "
                f"which java did (python={hero.unparsed_sections} "
                f"java={fixture['unparsed_sections']})"
            )

    assert len(mismatches) == 0, (
        f"{fixture_path.stem}: {len(mismatches)} mismatches:\n"
        + "\n".join(mismatches[:10])
    )


def test_totals_residual_ledger_is_not_stale():
    """Every ledger entry must still actually mismatch — fixed characters must be removed (ratchet).

    When the engine is improved and a character now passes, remove it from
    oracle_known_residuals.json.  Fail here means a free win: delete the entry.
    """
    residuals = _residuals_doc.get("residuals", {})
    still_wrong = []
    now_passing = []

    loader = HDCLoader()
    fixture_dir = FIXTURE_DIR

    for stem, entry in residuals.items():
        fixture_path = fixture_dir / f"{stem}.json"
        if not fixture_path.exists():
            still_wrong.append(stem)  # fixture gone; leave for human cleanup
            continue

        fixture = json.loads(fixture_path.read_text())
        hdc_path = fixture.get("hdc_path", "")
        if not Path(hdc_path).exists():
            still_wrong.append(stem)
            continue

        try:
            hero = loader.load_file(hdc_path)
        except Exception:
            still_wrong.append(stem)
            continue

        java_total = fixture.get("total_points")
        java_avail = fixture.get("available_points")

        total_ok = java_total is None or abs(hero.total_points - java_total) <= 0.01
        avail_ok = java_avail is None or abs(hero.available_points - java_avail) <= 0.01

        if total_ok and avail_ok:
            now_passing.append(stem)
        else:
            still_wrong.append(stem)

    assert len(now_passing) == 0, (
        f"{len(now_passing)} ledger entries now PASS — remove them from "
        f"oracle_known_residuals.json (ratchet):\n"
        + "\n".join(f"  remove: {s}" for s in now_passing[:20])
    )
