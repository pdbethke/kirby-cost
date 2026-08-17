"""Re-dump the bestiary HDC corpus to JSON with the fixed parser.

XML is a dead format here — JSON is the canonical character shape.
This script walks every HDC file under the resources tree, parses
it via the (now-fixed) HDCParser, and writes a sibling .hdc.json
file. It overwrites existing JSON dumps.

Why we need this: the previous parser dropped MODIFIER children of
DISAD elements during parse, so the existing .hdc.json files have
incomplete VULNERABILITY data (no MULTIPLIER 'TWICEBODY' OPTIONID),
which prevented downstream importers (kirby-api) from surfacing the
×2 BODY damage flag to the combat resolver.

Usage:
    venv/bin/python scripts/redump_character_json.py \
        --root /path/to/resources \
        [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from kirby_cost.io.hdc_parser import HDCParser


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root", required=True,
        help="Top of the HDC corpus to walk (e.g. champions-campaign-manager/resources)",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"error: --root {root} does not exist", file=sys.stderr)
        return 2

    parser = HDCParser()
    hdc_files = sorted(p for p in root.rglob("*.hdc") if "__MACOSX" not in p.parts)
    if args.limit:
        hdc_files = hdc_files[: args.limit]

    print(f"Walking {len(hdc_files)} HDC files under {root}...")
    succeeded = failed = unchanged = 0
    for hdc in hdc_files:
        json_path = hdc.with_suffix(hdc.suffix + ".json")
        try:
            data = parser.parse_file(str(hdc))
        except Exception as e:
            failed += 1
            print(f"  FAIL {hdc.name}: {e}", file=sys.stderr)
            continue
        new_text = json.dumps(data, indent=2, sort_keys=True)
        if json_path.exists():
            old_text = json_path.read_text()
            if old_text == new_text:
                unchanged += 1
                continue
        if not args.dry_run:
            json_path.write_text(new_text)
        succeeded += 1
        if succeeded % 100 == 0:
            print(f"  {succeeded} re-dumped...")

    print()
    print(f"re-dumped: {succeeded}, unchanged: {unchanged}, failed: {failed}")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
