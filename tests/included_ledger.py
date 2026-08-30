"""Rewrite `included_known_gaps.json` from a fresh matrix survey.

The ledger is SHRINK-ONLY, so it may never be edited by hand: a value typed in
by a human is a claim nobody checked, and a key added by hand defeats the whole
guard. This re-surveys every cell and rewrites the file from the answer.

    KIRBY_COST_HDT=/path/to/Main6E.hdt \
    KIRBY_COST_AUTHORED=/path/to/characters \
        venv/bin/python -m tests.included_ledger

What it does:

* **Refuses to write on a regression.** A cell that disagrees and is not
  already in the ledger exits 1 with the list -- that is a bug in the change
  being made, not a ledger update.
* **Drops the keys that now agree.** Exactly the ones the fix repaired.
* **PRESERVES a curated value.** A reason someone wrote -- "state-dependent;
  needs the authored-power matrix", "fixture keying: ...", the CustomPower
  END lead -- survives; only a raw survey line (one beginning `engine
  allowed=` or `raised `) is refreshed. Round 2 lost the three LINKED
  annotations to a naive rewrite before this rule existed.
* **Updates `_baseline`** with the new count.

Prints what fell, what remains, and the remaining cells by kind and modifier.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from datetime import date

from tests.test_included_matrix import LEDGER_PATH, _survey

#: A value the ledger's own tooling wrote, and may therefore overwrite.
#: Anything else is a human's reason and is kept verbatim.
_RAW_PREFIXES = ("engine allowed=", "raised ")


def is_curated(value: str) -> bool:
    return not value.startswith(_RAW_PREFIXES)


def _kind(value: str) -> str:
    if value.startswith("raised "):
        return "raised"
    engine = re.search(r"engine allowed=(\w+)", value)
    hd = re.search(r"HD allowed=(\w+)", value)
    if engine and hd:
        return "message-only" if engine.group(1) == hd.group(1) else "allowed-differs"
    return "curated"


def main() -> int:
    survey = _survey()
    doc = json.loads(LEDGER_PATH.read_text())
    old: dict[str, str] = doc["gaps"]

    regressions = sorted(set(survey) - set(old))
    if regressions:
        print(f"REGRESSION -- {len(regressions)} cells newly disagree; nothing written:")
        for key in regressions[:25]:
            print(f"  {key}\n      {survey[key]}")
        return 1

    fixed = sorted(set(old) - set(survey))
    doc["gaps"] = {
        key: (old[key] if is_curated(old[key]) else survey[key])
        for key in old
        if key in survey
    }
    stamp = date.today().isoformat()
    doc["_baseline"] = re.sub(
        r"now \d+ remain \([^)]*\)",
        f"now {len(survey)} remain ({stamp})",
        doc["_baseline"],
    )
    LEDGER_PATH.write_text(json.dumps(doc, indent=2) + "\n")

    print(f"fixed {len(fixed)}; {len(survey)} remain")
    print(sorted(collections.Counter(_kind(v) for v in doc["gaps"].values()).items()))
    print(collections.Counter(k.split("-on-")[0] for k in doc["gaps"]).most_common())
    return 0


if __name__ == "__main__":
    sys.exit(main())
