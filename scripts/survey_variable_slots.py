"""Survey which Multipower variable slots ladder (read-only report).

Usage: survey_variable_slots.py <dir of .hdc files> [<dir> ...]

Loads every .hdc beneath each directory with HDCLoader, walks each
Multipower's variable slots, and calls ``kirby_cost.engine.allocation.ladder``
on each.  Prints one line per slot (character, slot name, xmlid,
OK|NotLadderable) and then a count per xmlid.  It changes nothing; the
corpus is an argument because the .hdc files are licensed material that
never lives in this repo.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from kirby_cost.engine.allocation import NotLadderable, ladder
from kirby_cost.io.framework_access import framework_slots, slot_is_variable
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects.frameworks import is_multipower


def survey(paths: list[Path]):
    rows = []
    for path in paths:
        try:
            hero = HDCLoader().load_file(str(path))
        except Exception as exc:  # report, never hide, an unloadable file
            print(f"# SKIP {path.name}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        for fw in hero.powers:
            if not is_multipower(fw):
                continue
            for slot in framework_slots(hero, fw):
                if not slot_is_variable(fw, slot):
                    continue
                try:
                    ladder(slot)
                    verdict = "OK"
                except NotLadderable:
                    verdict = "NotLadderable"
                except Exception as exc:
                    verdict = f"ERROR {type(exc).__name__}: {exc}"
                rows.append((path.stem, slot.name or slot.alias or "", slot.xmlid, verdict))
    return rows


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    paths = sorted(p for d in argv for p in Path(d).rglob("*.hdc"))
    rows = survey(paths)
    for row in rows:
        print("\t".join(str(c) for c in row))
    tally = Counter((x, v) for _, _, x, v in rows)
    print(f"\n# {len(paths)} files, {len(rows)} variable slots")
    for (xmlid, verdict), n in sorted(tally.items()):
        print(f"{xmlid:20s} {verdict:14s} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
