#!/usr/bin/env python3
"""
Batch comparison: Java HD6 oracle vs Python cost engine.

Loads HDC files through the Java CLI, then replays each power's attributes
through the Python GenericObject cost chain. Reports every discrepancy.

Usage:
  python scripts/oracle_compare.py <file.hdc> [file2.hdc ...]
  python scripts/oracle_compare.py --all   # scan resources/ for all .hdc files
"""

import json
import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.adder import Adder
from kirby_cost.util.rounder import round_half_down

HD6CLI = str(Path(__file__).parent.parent.parent / "kirby-hd-oracle" / "hd6cli.sh")

# Characteristics have subclass overrides — track separately
CHAR_XMLIDS = {
    "STR", "DEX", "CON", "BODY", "INT", "EGO", "PRE", "COM",
    "PD", "ED", "SPD", "REC", "END", "STUN",
    "OCV", "DCV", "OMCV", "DMCV",
    "RUNNING", "SWIMMING", "LEAPING", "SIZE",
}


class ConcreteObject(GenericObject):
    pass

class ConcreteModifier(Modifier):
    pass

class ConcreteAdder(Adder):
    pass


def load_from_oracle(hdc_path: str) -> dict:
    """Load character through Java CLI oracle."""
    result = subprocess.run(
        [HD6CLI, hdc_path],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Oracle failed: {result.stderr}")
    return json.loads(result.stdout)


CLASS_MAP = {}

def _get_class_map():
    """Lazy-load class map for Java class name -> Python class."""
    if CLASS_MAP:
        return CLASS_MAP
    try:
        from kirby_cost.objects.characteristics.characteristic import Characteristic
        from kirby_cost.objects.powers.custom_power import CustomPower
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.objects.powers.endurance_reserve import EnduranceReserve
        from kirby_cost.objects.powers.force_wall import ForceWall
        from kirby_cost.objects.powers.force_field import ForceField
        from kirby_cost.objects.powers.duplication import Duplication
        from kirby_cost.objects.perks.follower import Follower
        from kirby_cost.objects.skills.skill import Skill
        from kirby_cost.objects.skills.knowledge_skill import KnowledgeSkill
        from kirby_cost.objects.skills.language import Language
        from kirby_cost.objects.skills.survival import Survival
        CLASS_MAP.update({
            'Characteristic': Characteristic,
            'Strength': Characteristic,
            'Dexterity': Characteristic,
            'Constitution': Characteristic,
            'Body': Characteristic,
            'Intelligence': Characteristic,
            'Ego': Characteristic,
            'Presence': Characteristic,
            'Comeliness': Characteristic,
            'PhysicalDefense': Characteristic,
            'EnergyDefense': Characteristic,
            'Speed': Characteristic,
            'Recovery': Characteristic,
            'Endurance': Characteristic,
            'Stun': Characteristic,
            'OCV': Characteristic,
            'DCV': Characteristic,
            'OMCV': Characteristic,
            'DMCV': Characteristic,
            'Running': Characteristic,
            'Swimming': Characteristic,
            'Leaping': Characteristic,
            'Size': Characteristic,
            'CustomPower': CustomPower,
            'NakedModifier': NakedModifier,
            'CompoundPower': CompoundPower,
            'EnduranceReserve': EnduranceReserve,
            'ForceWall': ForceWall,
            'ForceField': ForceField,
            'Duplication': Duplication,
            'Follower': Follower,
            # Skills
            'Skill': Skill,
            'KnowledgeSkill': KnowledgeSkill,
            'ProfessionalSkill': Skill,
            'ScienceSkill': KnowledgeSkill,
            'Language': Language,
            'Survival': Survival,
            'Navigation': Skill,
            'AnimalHandler': Skill,
            'Weaponsmith': Skill,
            'TransportFamiliarity': Skill,
            'CombatLevels': Skill,
            'MentalCombatLevels': Skill,
            'PenaltySkillLevels': Skill,
            'SkillLevels': Skill,
            'Gambling': Skill,
            'Forgery': Skill,
        })
    except ImportError:
        pass
    return CLASS_MAP


def build_object(power: dict):
    """Build a GenericObject from oracle data, using correct subclass when possible."""
    java_class = power.get("class", "")

    # CompoundPower: build from sub-powers
    sub_powers = power.get("sub_powers", [])
    if java_class == "CompoundPower" and sub_powers:
        return _build_compound_power(power)

    cls_map = _get_class_map()
    python_cls = cls_map.get(java_class)

    if python_cls:
        try:
            obj = python_cls(power["xmlid"])
        except TypeError:
            try:
                obj = python_cls()
            except Exception:
                obj = ConcreteObject()
        obj.xmlid = power["xmlid"]
    else:
        obj = ConcreteObject()
    obj.base_cost = power["base_cost"]
    obj.levels = power["levels"]
    obj.level_value = power["level_value"]
    obj.level_cost = power["level_cost"]
    obj.xmlid = power["xmlid"]

    # Set is_power from fixture (if available)
    if power.get("is_power") and hasattr(obj, '_is_power'):
        obj._is_power = True

    # Add adders with full detail
    for ad in power["adders"]:
        adder = ConcreteAdder()
        adder.base_cost = ad.get("real_cost", ad.get("base_cost", 0.0))
        adder.xmlid = ad["xmlid"]
        adder._required = ad.get("required", True)
        adder._selected = ad.get("selected", True)
        obj.assigned_adders.append(adder)

    # Add modifiers (use total_value as base_cost for simple replay)
    for md in power["modifiers"]:
        mod = ConcreteModifier()
        mod.base_cost = md["total_value"]
        mod.xmlid = md["xmlid"]
        # Set private flag from fixture (critical for NakedModifier cost calc)
        if md.get("is_private"):
            mod.private_mod = True
        obj.assigned_modifiers.append(mod)

    # Set up parent list (framework) if present
    _setup_parent_list(obj, power)

    return obj


def _build_compound_power(power: dict):
    """Build a CompoundPower with sub-powers."""
    try:
        from kirby_cost.objects.powers.compound_power import CompoundPower
        cp = CompoundPower()
    except ImportError:
        cp = ConcreteObject()
        return cp

    cp.xmlid = power["xmlid"]
    cp.base_cost = power["base_cost"]
    cp.levels = power["levels"]
    cp.level_value = power["level_value"]
    cp.level_cost = power["level_cost"]

    # Build each sub-power recursively
    for sp_data in power.get("sub_powers", []):
        sub = build_object(sp_data)
        cp.powers.append(sub)

    # Parent list
    _setup_parent_list(cp, power)

    # Modifiers on the compound power itself
    for md in power["modifiers"]:
        mod = ConcreteModifier()
        mod.base_cost = md["total_value"]
        mod.xmlid = md["xmlid"]
        cp.assigned_modifiers.append(mod)

    return cp


def _setup_parent_list(obj, power: dict):
    """Set up parent list (framework) from fixture data."""
    parent_mods = power.get("parent_modifiers", [])
    parent_class = power.get("parent_list_class", "")
    if power.get("parent_list_id") is not None:
        parent = ConcreteObject()
        parent.xmlid = power.get("parent_list_xmlid", "GENERIC_OBJECT")
        if parent_class == "Multipower":
            parent.xmlid = "MULTIPOWER"
        elif parent_class == "ElementalControl":
            parent.xmlid = "ELEMENTALCONTROL"
        for pm in parent_mods:
            pmod = ConcreteModifier()
            pmod.base_cost = pm["total_value"]
            pmod.xmlid = pm["xmlid"]
            parent.assigned_modifiers.append(pmod)
        obj.parent = parent
        # Objects in a framework are power-based
        if hasattr(obj, '_is_power'):
            obj._is_power = True


def compare_power(power: dict, section: str) -> list:
    """Compare one power's costs. Returns list of discrepancy dicts."""
    issues = []
    name = power.get("name") or power["xmlid"]
    java_class = power.get("class", "?")

    # Skip framework containers (Multipower, VPP, EC, List)
    if java_class in ("Multipower", "VariablePowerPool", "ElementalControl", "List"):
        return issues
    if power["xmlid"] == "GENERIC_OBJECT" and java_class == "List":
        return issues

    # Build Python object
    obj = build_object(power)

    # Items in the "powers" section are power-based
    if section == "powers" and hasattr(obj, '_is_power') and not obj._is_power:
        obj._is_power = True

    # Compare total_cost
    py_total = obj.total_cost
    java_total = power["total_cost"]
    if abs(py_total - java_total) > 0.01:
        issues.append({
            "field": "total_cost",
            "name": name,
            "xmlid": power["xmlid"],
            "class": java_class,
            "section": section,
            "python": py_total,
            "java": java_total,
            "delta": py_total - java_total,
        })

    # Compare active_cost (only if total matches — otherwise active will cascade)
    if abs(py_total - java_total) <= 0.01:
        py_active = obj.active_cost
        java_active = power["active_cost"]
        if abs(py_active - java_active) > 0.01:
            issues.append({
                "field": "active_cost",
                "name": name,
                "xmlid": power["xmlid"],
                "class": java_class,
                "section": section,
                "python": py_active,
                "java": java_active,
                "delta": py_active - java_active,
            })

        # Compare real_cost
        if abs(py_active - java_active) <= 0.01:
            py_real = obj.real_cost_pre_list
            java_real = power["real_cost"]
            if abs(py_real - java_real) > 0.01:
                has_parent = bool(power.get("parent_modifiers"))
                issues.append({
                    "field": "real_cost",
                    "name": name,
                    "xmlid": power["xmlid"],
                    "class": java_class,
                    "section": section,
                    "python": py_real,
                    "java": java_real,
                    "delta": py_real - java_real,
                    "note": "has parent list" if has_parent else "",
                })

    return issues


def compare_file(hdc_path: str) -> dict:
    """Compare all costs in one HDC file. Returns summary."""
    data = load_from_oracle(hdc_path)
    all_issues = []
    total_powers = 0
    matched = 0

    for section in ("characteristics", "skills", "powers", "perks", "talents", "complications"):
        for power in data.get(section, []):
            total_powers += 1
            issues = compare_power(power, section)
            if issues:
                all_issues.extend(issues)
            else:
                matched += 1

    return {
        "file": hdc_path,
        "name": data.get("name", "?"),
        "total": total_powers,
        "matched": matched,
        "issues": all_issues,
    }


def find_all_hdc(base_dir: str) -> list:
    """Find all .hdc files recursively."""
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        if "__MACOSX" in root:
            continue
        for f in filenames:
            if f.endswith(".hdc"):
                files.append(os.path.join(root, f))
    return sorted(files)


def main():
    if len(sys.argv) < 2:
        print("Usage: oracle_compare.py <file.hdc> [file2.hdc ...] | --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        base = str(Path(__file__).parent.parent.parent / "champions-campaign-manager" / "resources")
        files = find_all_hdc(base)
        # Also add Wipeout
        wipeout = str(Path(__file__).parent.parent.parent / "Champions Legacy" / "thowback" / "champions-rules-db" / "successful_exports" / "Wipeout_100percent.hdc")
        if os.path.exists(wipeout):
            files.insert(0, wipeout)
        print(f"Found {len(files)} HDC files")
    else:
        files = sys.argv[1:]

    grand_total = 0
    grand_matched = 0
    grand_issues = []
    issue_classes = {}  # Track which Java classes cause issues

    for f in files:
        try:
            result = compare_file(f)
        except Exception as e:
            print(f"  SKIP {os.path.basename(f)}: {e}")
            continue

        grand_total += result["total"]
        grand_matched += result["matched"]
        grand_issues.extend(result["issues"])

        pct = (result["matched"] / result["total"] * 100) if result["total"] > 0 else 100
        status = "✓" if len(result["issues"]) == 0 else "✗"
        print(f"  {status} {result['name']:40s}  {result['matched']}/{result['total']} matched  ({len(result['issues'])} issues)")

        for issue in result["issues"]:
            cls = issue.get("class", "?")
            issue_classes[cls] = issue_classes.get(cls, 0) + 1

    print()
    print("=" * 60)
    pct = (grand_matched / grand_total * 100) if grand_total > 0 else 100
    print(f"TOTAL: {grand_matched}/{grand_total} matched ({pct:.1f}%)")
    print(f"ISSUES: {len(grand_issues)}")

    if issue_classes:
        print()
        print("Issues by Java class:")
        for cls, count in sorted(issue_classes.items(), key=lambda x: -x[1]):
            print(f"  {cls:30s} {count} issues")

    if grand_issues:
        print()
        print("Sample discrepancies:")
        shown = set()
        for issue in grand_issues[:30]:
            key = f"{issue['xmlid']}:{issue['field']}:{issue.get('class','?')}"
            if key in shown:
                continue
            shown.add(key)
            note = f"  ({issue.get('note', '')})" if issue.get('note') else ""
            print(f"  {issue['name']:30s} {issue['field']:12s} py={issue['python']:8.1f} java={issue['java']:8.1f} delta={issue['delta']:+.1f}  class={issue.get('class','?')}{note}")


if __name__ == "__main__":
    main()
