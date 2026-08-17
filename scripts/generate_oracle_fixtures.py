"""Generate per-character oracle fixture files from the Java HD6 CLI.

The output is the project's source of truth, so regenerating it is a
deliberate act, not routine maintenance. It has happened once for a real
reason: on 2026-08-17 the headless fork was found unable to resolve any
``builtIn.`` template name, so every fixture generated between 2026-04-08 and
then had costed its character against Main6E no matter which template the file
named. 8 of 655 fixtures moved when that was fixed.

This used to say "run once, output is immutable — the Java oracle never
changes". The oracle is a program we forked; it changes when we fix it. What
must not change quietly is the *engine's* agreement with it, which is why:

**Before regenerating, capture the current oracle output and diff it.** A
regeneration that silently rewrites fixtures can turn an engine bug into
"parity" without anyone noticing. Expect an explicit, explainable set of
changed files, and if you cannot explain one, stop.

Usage:
    venv/bin/python scripts/generate_oracle_fixtures.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Workspace root is the directory containing this repo and its siblings
# (kirby-hd-oracle, champions-campaign-manager). Derived, not
# hardcoded: the old hardcoded "Champions Campaign Manager" path went stale
# when the workspace was renamed to Kirby, leaving every fixture's hdc_path
# dead — and the whole fixture suite silently skipping.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_WORKSPACE_ROOT = _PROJECT_ROOT.parent
RESOURCE_DIR = _WORKSPACE_ROOT / "champions-campaign-manager" / "resources"
HD6CLI = str(_WORKSPACE_ROOT / "kirby-hd-oracle" / "hd6cli.sh")
OUTPUT_DIR = _PROJECT_ROOT / "tests" / "fixtures" / "oracle"


def generate():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    errors = 0

    for root, dirs, files in os.walk(RESOURCE_DIR):
        if "__MACOSX" in root:
            continue
        for f in files:
            if not f.endswith(".hdc") or "CV3" in f:
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, RESOURCE_DIR)
            out_name = rel.replace(os.sep, "__").replace(".hdc", ".json")
            out_path = OUTPUT_DIR / out_name

            try:
                result = subprocess.run(
                    [HD6CLI, path], capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0 or not result.stdout.strip():
                    errors += 1
                    continue
                idx = result.stdout.find("{")
                if idx < 0:
                    errors += 1
                    continue
                oracle_data = json.loads(result.stdout[idx:])
                fixture = {
                    "hdc_path": path,
                    "relative_path": rel,
                    **oracle_data,
                }
                out_path.write_text(json.dumps(fixture, indent=2))
                total += 1
                print(f"  [{total}] {out_name}")
            except Exception as e:
                errors += 1
                print(f"  ERROR {f}: {e}", file=sys.stderr)

    print(f"\nGenerated {total} fixtures ({errors} errors)")


if __name__ == "__main__":
    generate()
