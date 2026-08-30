"""Rewrite a `*_known_gaps.json` ledger from a fresh matrix survey.

The ledger is SHRINK-ONLY, so it may never be edited by hand: a value typed in
by a human is a claim nobody checked, and a key added by hand defeats the whole
guard. This re-surveys every cell and rewrites the file from the answer.

    KIRBY_COST_HDT=/path/to/Main6E.hdt \
    KIRBY_COST_AUTHORED=/path/to/characters \
        venv/bin/python -m tests.included_ledger              # prototype matrix (default)
        venv/bin/python -m tests.included_ledger --stateful   # stateful matrix (Task 3)
        venv/bin/python -m tests.included_ledger --seed       # one-time baseline write

``--accept-new`` (with the default path): ADD newly disagreeing cells as raw lines
instead of refusing -- for the case where an upstream fix or a regenerated fixture
lets HD's question reach rules it never reached before. Curated values are kept.

What it does (default, no ``--seed``):

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

``--seed`` writes the ledger from scratch: every currently-disagreeing cell,
as a raw survey line, with no comparison against an existing file (there may
not be one, or a fixture re-key may have moved every key at once -- neither is
a regression of the engine). This is the baseline write: used once to start a
ledger, and used again only when the fixture itself is regenerated (a re-key,
a new state added to the sink) -- never as a shortcut around the shrink-only
path. Every other write goes through the normal (non-seed) path, which can
only shrink the file; curated values in that file are hand-written reasons a
person typed in, and the tool preserves them verbatim (see below).

Prints what fell (or was seeded), what remains, and the remaining cells by
kind and by modifier.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from datetime import date

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


def _prototype_config():
    from tests.matrix_support import cells
    from tests.test_included_matrix import LEDGER_PATH, _survey
    return LEDGER_PATH, _survey, (lambda k: k.split("-on-")[0]), len(cells())


def _stateful_config():
    from tests.matrix_support import stateful_cells
    from tests.test_included_stateful import LEDGER_PATH, _survey
    return LEDGER_PATH, _survey, (lambda k: k.split(":")[2]), len(stateful_cells())


def main(argv: list[str]) -> int:
    stateful = "--stateful" in argv
    seed = "--seed" in argv
    accept_new = "--accept-new" in argv

    ledger_path, survey_fn, modifier_of, total = (_stateful_config() if stateful else _prototype_config())
    survey = survey_fn()
    stamp = date.today().isoformat()

    if seed:
        doc = {
            "_comment": "SHRINK-ONLY. Cells where the engine's included() disagrees with Hero "
                        "Designer's, with what each side said. Written once as the raw survey "
                        f"baseline ({stamp}); every later commit may only remove entries. The "
                        "target is empty.",
            "_baseline": f"{len(survey)} of {total} cells disagree ({stamp})",
            "gaps": dict(sorted(survey.items())),
        }
        ledger_path.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"seeded {len(survey)} of {total:,}")
        print(sorted(collections.Counter(_kind(v) for v in doc["gaps"].values()).items()))
        print(collections.Counter(modifier_of(k) for k in doc["gaps"]).most_common())
        return 0

    doc = json.loads(ledger_path.read_text())
    old: dict[str, str] = doc["gaps"]

    regressions = sorted(set(survey) - set(old))
    if regressions and not accept_new:
        print(f"REGRESSION -- {len(regressions)} cells newly disagree; nothing written:")
        for key in regressions[:25]:
            print(f"  {key}\n      {survey[key]}")
        return 1
    if regressions and accept_new:
        print(f"accepting {len(regressions)} newly disagreeing cells as raw lines (fixture regenerated / an upstream fix reached new rules):")
        for key in regressions:
            print(f"  {key}")

    fixed = sorted(set(old) - set(survey))
    doc["gaps"] = {
        key: (old[key] if key in old and is_curated(old[key]) else survey[key])
        for key in list(old) + [k for k in survey if k not in old]
        if key in survey
    }
    clause = f"now {len(survey)} remain ({stamp})"
    if re.search(r"now \d+ remain \([^)]*\)", doc["_baseline"]):
        doc["_baseline"] = re.sub(r"now \d+ remain \([^)]*\)", clause, doc["_baseline"])
    else:
        doc["_baseline"] = f"{doc['_baseline']}; {clause}"
    ledger_path.write_text(json.dumps(doc, indent=2) + "\n")

    print(f"fixed {len(fixed)}; {len(survey)} remain")
    print(sorted(collections.Counter(_kind(v) for v in doc["gaps"].values()).items()))
    print(collections.Counter(modifier_of(k) for k in doc["gaps"]).most_common())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
