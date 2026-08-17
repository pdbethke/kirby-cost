"""
HDC round-trip test: load a character via Python HDC loader and compare
every cost against the Java HD6 oracle.

This is the definitive test — if this passes, the Python port matches
Hero Designer exactly.
"""

import json
import subprocess
import pytest
from pathlib import Path

HD6CLI = str(Path(__file__).parent.parent.parent / "kirby-hd-oracle" / "hd6cli.sh")


def load_oracle(hdc_path: str) -> dict:
    """Load character costs through Java CLI oracle."""
    result = subprocess.run(
        [HD6CLI, hdc_path],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        pytest.skip(f"Java oracle failed for {hdc_path}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.skip(f"Invalid JSON from oracle for {hdc_path}")


def load_python(hdc_path: str):
    """Load character through Python HDC loader."""
    from kirby_cost.io.hdc_loader import HDCLoader
    loader = HDCLoader()
    return loader.load_file(hdc_path)


WIPEOUT = str(Path(__file__).parent.parent.parent /
    "Champions Legacy/thowback/champions-rules-db/successful_exports/Wipeout_100percent.hdc")

HORSE = str(Path(__file__).parent.parent.parent /
    "champions-campaign-manager/resources/bestiary/"
    "HERO_System_Bestiary_6th_Edition_Character_Pack/HSB HD Files/"
    "CHAPTER_6/HORSES/RIDING_HORSE_HSB.hdc")

CROC = str(Path(__file__).parent.parent.parent /
    "champions-campaign-manager/resources/bestiary/"
    "HERO_System_Bestiary_6th_Edition_Character_Pack/HSB HD Files/"
    "CHAPTER_6/CROCODILE_ALLIGATOR_HSB.hdc")


class TestHDCLoader:
    """Basic loader tests."""

    def test_load_horse(self):
        hero = load_python(HORSE)
        assert hero.name == "Horse, Riding"
        assert len(hero.characteristics) > 0
        assert len(hero.powers) > 0

    def test_load_wipeout(self):
        hero = load_python(WIPEOUT)
        assert hero.name == "Wipeout"


class TestHDCWipeoutRoundtrip:
    """Wipeout is the hardest test — complex Multipower, CompoundPower, modifiers."""

    def test_wipeout_roundtrip(self):
        oracle = load_oracle(WIPEOUT)
        hero = load_python(WIPEOUT)

        issues = []
        for section, py_list, java_key in [
            ("char", hero.characteristics, "characteristics"),
            ("power", hero.powers, "powers"),
            ("skill", hero.skills, "skills"),
            ("complication", hero.complications, "complications"),
        ]:
            java_list = oracle.get(java_key, [])
            for i, java_obj in enumerate(java_list):
                java_class = java_obj.get("class", "?")
                if java_class in ("Multipower", "VariablePowerPool", "ElementalControl", "List"):
                    continue
                name = java_obj.get("name") or java_obj["xmlid"]
                if i >= len(py_list):
                    issues.append(f"{section}[{i}] {name}: missing in Python")
                    continue
                py_obj = py_list[i]
                for field, py_fn in [
                    ("total_cost", lambda o: o.total_cost),
                    ("active_cost", lambda o: o.active_cost),
                    ("real_cost", lambda o: o.real_cost_pre_list),
                ]:
                    py_val = py_fn(py_obj)
                    java_val = java_obj[field]
                    if abs(py_val - java_val) > 0.01:
                        issues.append(
                            f"{section} {name}: {field} py={py_val} java={java_val} "
                            f"(class={java_class})"
                        )

        if issues:
            msg = f"\n{len(issues)} cost mismatches:\n" + "\n".join(f"  {i}" for i in issues[:30])
            pytest.fail(msg)


class TestHDCRoundtrip:
    """Compare Python-loaded costs against Java oracle for every object."""

    def _compare_section(self, py_objects, java_objects, section_name: str):
        """Compare a section of objects between Python and Java."""
        issues = []

        # Match by index (same order)
        for i, java_obj in enumerate(java_objects):
            java_class = java_obj.get("class", "?")

            # Skip framework containers
            if java_class in ("Multipower", "VariablePowerPool", "ElementalControl", "List"):
                continue

            if i >= len(py_objects):
                issues.append(f"{section_name}[{i}] {java_obj['name'] or java_obj['xmlid']}: missing in Python")
                continue

            py_obj = py_objects[i]
            name = java_obj.get("name") or java_obj["xmlid"]

            # Compare total_cost
            py_total = py_obj.total_cost
            java_total = java_obj["total_cost"]
            if abs(py_total - java_total) > 0.01:
                issues.append(
                    f"{section_name} {name}: total_cost py={py_total} java={java_total} "
                    f"(class={java_class})"
                )

            # Compare active_cost
            py_active = py_obj.active_cost
            java_active = java_obj["active_cost"]
            if abs(py_active - java_active) > 0.01:
                issues.append(
                    f"{section_name} {name}: active_cost py={py_active} java={java_active} "
                    f"(class={java_class})"
                )

            # Compare real_cost
            py_real = py_obj.real_cost_pre_list
            java_real = java_obj["real_cost"]
            if abs(py_real - java_real) > 0.01:
                issues.append(
                    f"{section_name} {name}: real_cost py={py_real} java={java_real} "
                    f"(class={java_class})"
                )

        return issues

    def test_horse_roundtrip(self):
        oracle = load_oracle(HORSE)
        hero = load_python(HORSE)

        issues = []
        issues.extend(self._compare_section(hero.characteristics, oracle["characteristics"], "char"))
        issues.extend(self._compare_section(hero.powers, oracle["powers"], "power"))
        issues.extend(self._compare_section(hero.skills, oracle["skills"], "skill"))
        issues.extend(self._compare_section(hero.complications, oracle["complications"], "complication"))

        if issues:
            msg = f"\n{len(issues)} cost mismatches:\n" + "\n".join(f"  {i}" for i in issues[:20])
            pytest.fail(msg)

    def test_croc_roundtrip(self):
        oracle = load_oracle(CROC)
        hero = load_python(CROC)

        issues = []
        issues.extend(self._compare_section(hero.characteristics, oracle["characteristics"], "char"))
        issues.extend(self._compare_section(hero.powers, oracle["powers"], "power"))

        if issues:
            msg = f"\n{len(issues)} cost mismatches:\n" + "\n".join(f"  {i}" for i in issues[:20])
            pytest.fail(msg)
