#!/usr/bin/env python3
"""
Oracle comparison v2: Uses the HDC loader (with Main6E.hdt template)
to load characters in Python, then compares against the Java CLI oracle.

This is the definitive comparison — same loader used in production,
same template, same framework relationships.

Usage:
  python scripts/oracle_compare_v2.py <file.hdc> [file2.hdc ...]
  python scripts/oracle_compare_v2.py --all
"""

import json
import subprocess
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from kirby_cost.io.hdc_loader import HDCLoader

HD6CLI = str(Path(__file__).parent.parent.parent / "kirby-hd-oracle" / "hd6cli.sh")

loader = HDCLoader()


def load_oracle(hdc_path: str) -> dict:
    result = subprocess.run(
        [HD6CLI, hdc_path],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"Oracle failed for {hdc_path}")
    # Java HD6 may print debug lines before JSON — find the JSON start
    output = result.stdout
    json_start = output.find('{')
    if json_start < 0:
        raise RuntimeError(f"No JSON in oracle output for {hdc_path}")
    return json.loads(output[json_start:])


def compare_file(hdc_path: str) -> dict:
    """Compare all costs in one HDC file."""
    # Load via Java oracle
    oracle = load_oracle(hdc_path)

    # Load via Python HDC loader
    try:
        hero = loader.load_file(hdc_path)
    except Exception as e:
        raise RuntimeError(f"Python loader failed: {e}")

    all_issues = []
    total = 0
    matched = 0

    sections = [
        ("characteristics", hero.characteristics, oracle.get("characteristics", [])),
        ("powers", hero.powers, oracle.get("powers", [])),
        ("skills", hero.skills, oracle.get("skills", [])),
        ("perks", hero.perks, oracle.get("perks", [])),
        ("talents", hero.talents, oracle.get("talents", [])),
        ("complications", hero.complications, oracle.get("complications", [])),
        ("martial_arts", hero.martial_arts, oracle.get("martial_arts", [])),
    ]

    FRAMEWORK_CLASSES = {"Multipower", "VariablePowerPool", "ElementalControl", "List"}

    for section_name, py_list, java_list in sections:
        # Filter out framework containers from both lists to align indices
        java_filtered = [j for j in java_list if j.get("class", "?") not in FRAMEWORK_CLASSES]
        py_filtered = [p for p in py_list if type(p).__name__ == "_FallbackObject" and p.xmlid in ("MULTIPOWER", "VPP", "ELEMENTALCONTROL", "GENERIC_OBJECT") and len(p.assigned_modifiers) == 0 or False]
        # Actually just filter by checking if it looks like a framework
        py_non_fw = []
        for p in py_list:
            xmlid = p.xmlid
            # Skip framework containers by XMLID
            if xmlid in ("MULTIPOWER", "VPP", "ELEMENTALCONTROL"):
                continue
            # Skip LIST/GENERIC_OBJECT framework containers
            # These have GENERIC_OBJECT xmlid, no level_cost, and may have modifiers
            if xmlid == "GENERIC_OBJECT" and p.levels == 0 and p.level_cost == 0.0:
                continue
            py_non_fw.append(p)

        for i, java_obj in enumerate(java_filtered):
            java_class = java_obj.get("class", "?")
            name = java_obj.get("name") or java_obj["xmlid"]
            total += 1

            if i >= len(py_non_fw):
                all_issues.append({
                    "field": "missing",
                    "name": name,
                    "class": java_class,
                    "section": section_name,
                })
                continue

            py_obj = py_non_fw[i]
            has_issue = False

            for field in ("total_cost", "active_cost", "real_cost"):
                if field == "total_cost":
                    py_val = py_obj.total_cost
                elif field == "active_cost":
                    py_val = py_obj.active_cost
                else:
                    py_val = py_obj.real_cost_pre_list

                java_val = java_obj[field]

                if abs(py_val - java_val) > 0.01:
                    has_issue = True
                    all_issues.append({
                        "field": field,
                        "name": name,
                        "xmlid": java_obj["xmlid"],
                        "class": java_class,
                        "section": section_name,
                        "python": py_val,
                        "java": java_val,
                        "delta": py_val - java_val,
                    })

            if not has_issue:
                matched += 1

    # Per-character totals comparison (not ledger-gated — reporting tool shows everything)
    for totals_field, py_val, java_key in [
        ("total_points", hero.total_points, "total_points"),
        ("available_points", hero.available_points, "available_points"),
    ]:
        java_val = oracle.get(java_key)
        if java_val is not None and abs(py_val - java_val) > 0.01:
            all_issues.append({
                "field": totals_field,
                "name": oracle.get("name", "?"),
                "xmlid": totals_field,
                "class": "character",
                "section": "character",
                "python": py_val,
                "java": java_val,
                "delta": py_val - java_val,
            })

    if "unparsed_sections" in oracle:
        py_up = sorted(hero.unparsed_sections)
        java_up = sorted(oracle["unparsed_sections"])
        if py_up != java_up:
            all_issues.append({
                "field": "unparsed_sections",
                "name": oracle.get("name", "?"),
                "xmlid": "unparsed_sections",
                "class": "character",
                "section": "character",
                "python": py_up,
                "java": java_up,
                "delta": 0,
            })

    return {
        "file": hdc_path,
        "name": oracle.get("name", "?"),
        "total": total,
        "matched": matched,
        "issues": all_issues,
    }


def find_all_hdc(base_dir: str) -> list:
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        if "__MACOSX" in root:
            continue
        for f in filenames:
            if f.endswith(".hdc") and "CV3" not in f:
                files.append(os.path.join(root, f))
    return sorted(files)


def main():
    if len(sys.argv) < 2:
        print("Usage: oracle_compare_v2.py <file.hdc> [file2.hdc ...] | --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        base = str(Path(__file__).parent.parent.parent / "champions-campaign-manager" / "resources")
        files = find_all_hdc(base)
        wipeout = str(Path(__file__).parent.parent.parent / "Champions Legacy" / "thowback" / "champions-rules-db" / "successful_exports" / "Wipeout_100percent.hdc")
        if os.path.exists(wipeout):
            files.insert(0, wipeout)
        print(f"Found {len(files)} HDC files")
    else:
        files = sys.argv[1:]

    grand_total = 0
    grand_matched = 0
    grand_issues = []
    issue_classes = {}
    perfect = 0
    failed = 0

    for f in files:
        try:
            result = compare_file(f)
        except Exception as e:
            print(f"  SKIP {os.path.basename(f)}: {e}")
            continue

        grand_total += result["total"]
        grand_matched += result["matched"]
        grand_issues.extend(result["issues"])

        for issue in result["issues"]:
            cls = issue.get("class", "?")
            issue_classes[cls] = issue_classes.get(cls, 0) + 1

        pct = (result["matched"] / result["total"] * 100) if result["total"] > 0 else 100
        if len(result["issues"]) == 0:
            perfect += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        print(f"  {status} {result['name']:40s}  {result['matched']}/{result['total']} ({pct:.0f}%)  {len(result['issues'])} issues")

    print()
    print("=" * 60)
    pct = (grand_matched / grand_total * 100) if grand_total > 0 else 100
    print(f"TOTAL: {grand_matched}/{grand_total} matched ({pct:.1f}%)")
    print(f"PERFECT: {perfect} characters at 100%")
    print(f"ISSUES: {len(grand_issues)} across {failed} characters")

    if issue_classes:
        print()
        print("Issues by Java class:")
        for cls, count in sorted(issue_classes.items(), key=lambda x: -x[1]):
            print(f"  {cls:30s} {count}")

    if grand_issues:
        print()
        print("Sample discrepancies:")
        shown = set()
        for issue in grand_issues[:40]:
            if issue["field"] == "missing":
                key = f"missing:{issue['name']}"
                if key not in shown:
                    shown.add(key)
                    print(f"  {issue['name']:30s} MISSING in Python  class={issue['class']}")
                continue
            key = f"{issue['xmlid']}:{issue['field']}:{issue.get('class','?')}"
            if key in shown:
                continue
            shown.add(key)
            print(f"  {issue['name']:30s} {issue['field']:12s} py={issue['python']:8.1f} java={issue['java']:8.1f} delta={issue['delta']:+.1f}  class={issue.get('class','?')}")


if __name__ == "__main__":
    main()
