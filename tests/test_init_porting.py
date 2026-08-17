"""Oracle-driven integration tests for init porting fixes.

Requires:
- Java HD6 CLI at the HD oracle harness/hd6cli.sh
- HDC resource files at the character-pack checkout/resources/
Tests skip gracefully when unavailable.
"""
from tests.corpus import hd6cli, corpus_root
import json
import os
import subprocess
import pytest
from pathlib import Path

RESOURCE_DIR = corpus_root() or Path("/nonexistent")
HD6CLI = str(hd6cli() or "/nonexistent/hd6cli.sh")

# The comparison harness wraps licensed HERO Designer source and is not public.
# Point KIRBY_COST_HD6CLI at it to run these; without it they skip.
pytestmark = pytest.mark.skipif(
    hd6cli() is None,
    reason="HD6 comparison CLI not configured (set KIRBY_COST_HD6CLI)",
)


def _hdc_files():
    """Yield all HDC file paths."""
    for root, dirs, files in os.walk(RESOURCE_DIR):
        if "__MACOSX" in root:
            continue
        for f in files:
            if f.endswith(".hdc") and "CV3" not in f:
                yield os.path.join(root, f)


def _oracle(hdc_path: str) -> dict:
    """Run Java oracle on an HDC file, return parsed JSON."""
    result = subprocess.run(
        [HD6CLI, hdc_path], capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        pytest.skip(f"Oracle failed for {hdc_path}")
    output = result.stdout
    idx = output.find("{")
    if idx < 0:
        pytest.skip(f"No JSON in oracle output for {hdc_path}")
    return json.loads(output[idx:])


def _find_hdc_with(xmlid: str) -> str:
    """Find first HDC file containing a given XMLID."""
    for path in _hdc_files():
        with open(path, "rb") as fh:
            if xmlid.encode() in fh.read():
                return path
    pytest.skip(f"No HDC with {xmlid} found")


def _compare_section(hero_list, oracle_list, section="powers"):
    """Compare Python objects against Java oracle, return list of (py, java) mismatches."""
    FW = {"Multipower", "VariablePowerPool", "ElementalControl", "List"}
    java_filtered = [j for j in oracle_list if j.get("class") not in FW]
    py_filtered = [p for p in hero_list
                   if p.xmlid not in ("MULTIPOWER", "VPP", "ELEMENTALCONTROL")
                   and not (p.xmlid == "GENERIC_OBJECT"
                            and p.levels == 0
                            and p.level_cost == 0.0)]
    mismatches = []
    for i, java_obj in enumerate(java_filtered):
        if i >= len(py_filtered):
            break
        py_obj = py_filtered[i]
        for field in ("total_cost", "active_cost", "real_cost"):
            py_val = (py_obj.total_cost if field == "total_cost"
                      else py_obj.active_cost if field == "active_cost"
                      else py_obj.real_cost_pre_list)
            if abs(py_val - java_obj[field]) > 0.01:
                mismatches.append((py_obj, java_obj, field))
                break
    return mismatches


class TestSensePowerCosts:
    """EnhancedPerception/Telescopic option alias resolution."""

    def test_enhanced_perception_costs_match_oracle(self):
        """All EP objects in a character should match Java costs."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with("ENHANCEDPERCEPTION")
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.powers, oracle.get("powers", []))
        ep_mismatches = [m for m in mismatches if m[1]["xmlid"] == "ENHANCEDPERCEPTION"]
        assert len(ep_mismatches) == 0, \
            f"EP mismatches: {[(m[1]['xmlid'], m[2], m[1][m[2]]) for m in ep_mismatches]}"

    def test_telescopic_costs_match_oracle(self):
        """All Telescopic objects in a character should match Java costs."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with("TELESCOPIC")
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.powers, oracle.get("powers", []))
        tel_mismatches = [m for m in mismatches if m[1]["xmlid"] == "TELESCOPIC"]
        assert len(tel_mismatches) == 0, \
            f"Telescopic mismatches: {[(m[1]['xmlid'], m[2], m[1][m[2]]) for m in tel_mismatches]}"


class TestAdderBasedSkillCosts:
    """Skills that use adder-based cost (Navigation, AnimalHandler, etc.)."""

    @pytest.mark.parametrize("xmlid", [
        "NAVIGATION", "ANIMAL_HANDLER", "GAMBLING", "WEAPONSMITH",
        "TRANSPORT_FAMILIARITY", "FORGERY",
    ])
    def test_adder_skill_costs_match_oracle(self, xmlid):
        """Adder-based skill cost should match Java oracle."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with(xmlid)
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.skills, oracle.get("skills", []))
        skill_mismatches = [m for m in mismatches if m[1]["xmlid"] == xmlid]
        assert len(skill_mismatches) == 0, \
            f"{xmlid} mismatches: {[(m[2], m[0].total_cost, m[1][m[2]]) for m in skill_mismatches]}"


class TestForceWallCosts:
    """ForceWall dimension level costs."""

    def test_force_wall_costs_match_oracle(self):
        """ForceWall with dimension levels should include their cost."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with("FORCEWALL")
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.powers, oracle.get("powers", []))
        fw_mismatches = [m for m in mismatches if m[1]["xmlid"] == "FORCEWALL"]
        assert len(fw_mismatches) == 0, \
            f"ForceWall mismatches: {[(m[2], m[0].total_cost, m[1][m[2]]) for m in fw_mismatches]}"


class TestEnduranceReserveCosts:
    """EnduranceReserve with recovery component."""

    def test_endurance_reserve_costs_match_oracle(self):
        """END Reserve should include recovery component cost."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with("ENDURANCERESERVE")
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.powers, oracle.get("powers", []))
        er_mismatches = [m for m in mismatches if m[1]["xmlid"] == "ENDURANCERESERVE"]
        assert len(er_mismatches) == 0, \
            f"EndRes mismatches: {[(m[2], m[0].total_cost, m[1][m[2]]) for m in er_mismatches]}"


class TestPerkAndPowerMapping:
    """Perk/power class mapping for correct cost calculation."""

    @pytest.mark.parametrize("xmlid,section", [
        ("FOLLOWER", "perks"),
        ("REPUTATION", "perks"),
        ("MONEY", "perks"),
        ("DAMAGEREDUCTION", "powers"),
    ])
    def test_class_costs_match_oracle(self, xmlid, section):
        """Mapped class should produce correct costs."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with(xmlid)
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        hero_list = getattr(hero, section)
        mismatches = _compare_section(hero_list, oracle.get(section, []))
        target_mismatches = [m for m in mismatches if m[1]["xmlid"] == xmlid]
        assert len(target_mismatches) == 0, \
            f"{xmlid} mismatches: {[(m[2], m[0].total_cost, m[1][m[2]]) for m in target_mismatches]}"
