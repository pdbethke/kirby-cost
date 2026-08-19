"""Which TEXT attributes are a user's own words, and which are just stale?

An HDC's ``TEXT`` is the one field that can carry wording HERO Designer did
not produce. HD stores it only when the user has typed over the generated
display string — ``setTextOutput`` keeps ``null`` when the text equals what
``getColumn2Output()`` would return, and ``getSaveXML`` writes the attribute
only when something is stored (GenericObject.java:1884, :1916).

That is HD's rule at the moment of SAVING. It says nothing about a file
written years and several HD versions ago, whose generator phrased things
differently. Such a TEXT is indistinguishable from a deliberate override by
looking at the document — both are just an attribute — and the difference
matters to anyone deciding whether it is safe to regenerate:

  * a genuine override is the user's intent, and destroying it is data loss;
  * a stale one is a fossil of an older generator, and preserving it forever
    means the character never picks up a corrected display string.

kirby-cost cannot tell them apart on its own, because it has no display layer:
``modifier_string`` and friends are ~120 deliberate stubs. The Java oracle can,
because it still has one. So this asks the oracle what HD would generate today
and compares.

Requires ``KIRBY_COST_HD6CLI`` to point at a build of the CLI that dumps
``column2_output`` and ``id``; without it there is nothing to compare against
and this exits saying so. Reports only — it changes no files.

Usage::

    python scripts/detect_text_overrides.py                # whole corpus
    python scripts/detect_text_overrides.py FILE.hdc ...   # named characters
    python scripts/detect_text_overrides.py --limit 50     # first 50
    python scripts/detect_text_overrides.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lxml import etree  # noqa: E402

from tests.corpus import corpus_root, hd6cli  # noqa: E402

#: Sections of the oracle dump that hold objects.
_SECTIONS = ("characteristics", "powers", "skills", "perks", "talents",
             "complications", "martial_arts", "equipment")

MATCH = "matches_hd"        # HD would generate this exactly; not an override
OVERRIDE = "user_override"  # HD would generate something else; the user's words
UNKNOWN = "unmatched"       # no oracle object with that ID; cannot say


def _decode(raw: bytes) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw[:4] == b"<\x00?\x00":
        return raw.decode("utf-16-le")
    if raw[:4] == b"\x00<\x00?":
        return raw.decode("utf-16-be")
    return raw.decode("utf-8")


def _parse(path: Path):
    text = _decode(path.read_bytes())
    if text.startswith("<?xml"):
        text = text[text.index("?>") + 2:].lstrip()
    parser = etree.XMLParser(recover=True)
    return etree.fromstring(text.encode("utf-8"), parser)


def stated_text(path: Path) -> dict[str, dict]:
    """{element ID: {text, xmlid, name}} for every element carrying a TEXT."""
    out: dict[str, dict] = {}
    for elem in _parse(path).iter():
        ident, text = elem.get("ID"), elem.get("TEXT")
        if ident and text:
            out[ident] = {"text": text, "xmlid": elem.get("XMLID") or elem.tag,
                          "name": elem.get("NAME") or ""}
    return out


def generated_text(cli: Path, path: Path) -> dict[str, str] | None:
    """{element ID: column2_output} as HD would generate it, or None."""
    try:
        proc = subprocess.run([str(cli), str(path)], capture_output=True,
                              text=True, timeout=120)
        dump = json.loads(proc.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None

    out: dict[str, str] = {}

    def walk(objects):
        for obj in objects or ():
            ident = obj.get("id")
            if ident is not None and obj.get("column2_output") is not None:
                out[str(ident)] = obj["column2_output"]
            walk(obj.get("sub_powers"))
            walk(obj.get("modifiers"))
            walk(obj.get("adders"))

    for section in _SECTIONS:
        walk(dump.get(section))
    return out


def classify(path: Path, cli: Path) -> list[dict]:
    """One row per TEXT the document carries."""
    stated = stated_text(path)
    if not stated:
        return []
    generated = generated_text(cli, path)
    if generated is None:
        return [{"file": path.name, "id": i, "verdict": UNKNOWN,
                 "reason": "oracle produced no usable dump", **v}
                for i, v in stated.items()]

    rows = []
    for ident, info in stated.items():
        hd = generated.get(ident)
        if hd is None:
            verdict, reason = UNKNOWN, "no object with this ID in the dump"
        elif hd.strip() == info["text"].strip():
            # HD strips TEXT on restore (GenericObject.java:3623), so trailing
            # whitespace is never the thing that makes an override.
            verdict, reason = MATCH, ""
        else:
            verdict, reason = OVERRIDE, ""
        rows.append({"file": path.name, "id": ident, "verdict": verdict,
                     "reason": reason, "generated": hd, **info})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", type=Path, help="write full rows here")
    ap.add_argument("--show", type=int, default=12,
                    help="how many overrides to print (0 for all)")
    args = ap.parse_args(argv)

    cli = hd6cli()
    if cli is None:
        print("No comparison CLI configured. This needs HERO Designer's own "
              "display output to compare against; set KIRBY_COST_HD6CLI.",
              file=sys.stderr)
        return 2

    files = args.files
    if not files:
        root = corpus_root()
        if root is None:
            print("No corpus configured (set KIRBY_COST_CORPUS), and no files "
                  "named on the command line.", file=sys.stderr)
            return 2
        files = sorted(f for f in root.rglob("*.hdc")
                       if not f.name.startswith("._"))

    # Only characters that carry a TEXT are worth an oracle run — it is a
    # subprocess per file, and 0.2% of objects carry one.
    files = [f for f in files if stated_text(f)]
    if args.limit:
        files = files[:args.limit]
    print(f"{len(files)} characters carry at least one TEXT; asking the oracle "
          f"what it would generate for each.", file=sys.stderr)

    rows: list[dict] = []
    for i, path in enumerate(files, 1):
        rows.extend(classify(path, cli))
        if i % 20 == 0:
            print(f"  {i}/{len(files)}", file=sys.stderr)

    counts = {v: sum(1 for r in rows if r["verdict"] == v)
              for v in (OVERRIDE, MATCH, UNKNOWN)}
    total = len(rows) or 1
    print(f"\n{len(rows)} TEXT attributes across {len(files)} characters")
    for verdict, label in ((OVERRIDE, "the user's own words"),
                           (MATCH, "identical to what HD generates"),
                           (UNKNOWN, "could not be matched")):
        n = counts[verdict]
        print(f"  {n:5d}  {100 * n / total:5.1f}%  {verdict:<14} {label}")

    shown = [r for r in rows if r["verdict"] == OVERRIDE]
    for row in (shown if args.show == 0 else shown[:args.show]):
        print(f"\n  {row['file']}  {row['xmlid']}"
              f"{'  ' + row['name'] if row['name'] else ''}")
        print(f"    document : {row['text']!r}")
        print(f"    HD writes: {row['generated']!r}")
    if args.show and len(shown) > args.show:
        print(f"\n  ... and {len(shown) - args.show} more "
              f"(--show 0 for all, --json to keep them)")

    if args.json:
        args.json.write_text(json.dumps(rows, indent=2))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
