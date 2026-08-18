"""Everything the document said, the export says back.

The oracle suite proves the engine COSTS a character the way HERO Designer
does. It says nothing about whether the character survives being written out
again, because it never writes one — and a character that reloads short of
what it was is wrong in a way no cost comparison can see.

Measured 2026-08-18, before any of this was fixed: of 794 corpus characters,
485 came back saying something different from what was read. A CUSTOMPOWER
lost all twelve attributes that define what it DOES; a Force Wall lost the
PD/ED/MD/POWD split HD costs it by; every character with a campaign
``<RULES>`` block lost the block entire. None of it failed loudly. The file
opened, and the character was quietly someone else.

So this asserts the whole property at once, over every character available:
**every element and every attribute the source stated is stated again by the
export, with the same value.** Not a sample of them, and not the ones somebody
remembered to list.

The ledger works like ``oracle_known_residuals.json``: shrink-only, with a
staleness ratchet. When a class starts round-tripping, its entry comes out in
the same commit — ``test_export_ledger_is_not_stale`` fails until it does, and
that failure is a free win, not a regression.

It has two lists, and the difference between them is the whole discipline:

``gaps``
    Defects. Known, not yet fixed, and each one a character that comes back
    saying less than it said. This list is meant to reach zero, and it has.

``matches_hd``
    Diffs HERO DESIGNER ITSELF produces on a re-save, so reproducing them is
    fidelity rather than damage. Each entry states the Java that does it,
    because "HD does this too" is exactly the excuse that would hide a real
    defect if it were ever accepted without one. Two entries, both normalising:
    HD trims TEXT (``textOutput = check.trim()``) and HD re-resolves an
    option's cost onto BASECOST after restoring it.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest
from lxml import etree

from tests.corpus import corpus_root

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.io.hdc_writer import hero_to_bytes

LEDGER_PATH = Path(__file__).parent / "fixtures" / "export_known_gaps.json"

pytestmark = pytest.mark.skipif(
    corpus_root() is None,
    reason="no character corpus configured (set KIRBY_COST_CORPUS)",
)


def _ledger() -> set[str]:
    """Every key the ledger accounts for — defects and HD's own normalising."""
    if not LEDGER_PATH.exists():
        return set()
    doc = json.loads(LEDGER_PATH.read_text())
    return set(doc.get("gaps", [])) | set(doc.get("matches_hd", []))


def _corpus_files() -> list[Path]:
    root = corpus_root()
    if root is None:
        return []
    # macOS AppleDouble sidecars (._NAME) are resource forks carrying no XML.
    # 727 of them sit in this corpus and are not characters.
    return sorted(f for f in root.rglob("*.hdc") if not f.name.startswith("._"))


def _decode(raw: bytes) -> str:
    """The loader's own detection, so the comparison reads what it read."""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw[:4] == b"<\x00?\x00":
        return raw.decode("utf-16-le")
    if raw[:4] == b"\x00<\x00?":
        return raw.decode("utf-16-be")
    return raw.decode("utf-8")


def _parse(raw: bytes) -> etree._Element:
    text = _decode(raw)
    if text.startswith("<?xml"):
        text = text[text.index("?>") + 2:].lstrip()
    parser = etree.XMLParser(recover=True, remove_blank_text=True)
    return etree.fromstring(text.encode("utf-8"), parser)


def _index(elem: etree._Element, path: str = "") -> dict:
    """Every element under ``elem``, keyed stably.

    Keyed by HD's own ``ID`` where the element has one, so a change of ORDER
    is one diff rather than a few hundred phantom attribute changes against
    whatever ended up in that position. Positional keys are the fallback for
    what HD does not id: the sections, CHARACTER_INFO, RULES, the prose.
    """
    out: dict = {}
    counter: collections.Counter = collections.Counter()
    for child in elem:
        if not isinstance(child.tag, str):
            continue
        counter[child.tag] += 1
        ident = child.get("ID")
        key = (f"{path}/#{ident}" if ident
               else f"{path}/{child.tag}[{counter[child.tag]}]")
        out[key] = child
        out.update(_index(child, key))
    return out


def _gap_key(elem: etree._Element, attr: str = "") -> str:
    """The ledger key for a diff: the class it belongs to, and what was lost.

    Keyed by class rather than by character, because these are class defects —
    every CUSTOMPOWER in the corpus loses the same twelve attributes, and a
    per-character ledger would have 164 entries for one missing declaration.
    """
    xmlid = elem.get("XMLID") or elem.tag
    return f"{elem.tag}:{xmlid}|{attr}" if attr else f"{elem.tag}:{xmlid}"


def _diff_document(original: etree._Element, exported: etree._Element) -> list:
    """(gap_key, detail) for everything the export failed to say back."""
    diffs = []
    o_map, n_map = _index(original), _index(exported)

    for key, oe in o_map.items():
        ne = n_map.get(key)
        if ne is None:
            diffs.append((_gap_key(oe), f"element dropped: {key}"))
            continue
        for attr, value in oe.attrib.items():
            if attr not in ne.attrib:
                diffs.append((_gap_key(oe, attr), f"{key} lost {attr}={value!r}"))
            elif ne.attrib[attr] != value:
                diffs.append((_gap_key(oe, attr),
                              f"{key} {attr}: {value!r} -> {ne.attrib[attr]!r}"))
        for attr, value in ne.attrib.items():
            if attr not in oe.attrib:
                diffs.append((_gap_key(oe, attr),
                              f"{key} gained {attr}={value!r} the source never stated"))
        # Order, not just presence. lxml writes attributes in the order they
        # were set, so a document that says the same things in a different
        # order is still a gratuitous diff against every file HD has produced —
        # and the one bug this whole file missed was an ordering one, caught by
        # tests/test_hdc_writer.py on a single character while 794 of them
        # reported clean.
        shared = [a for a in oe.attrib if a in ne.attrib]
        if shared != [a for a in ne.attrib if a in oe.attrib]:
            diffs.append((_gap_key(oe, "#order"), f"{key} attribute order changed"))
        o_text, n_text = (oe.text or "").strip(), (ne.text or "").strip()
        if o_text != n_text:
            diffs.append((_gap_key(oe, "#text"), f"{key} text changed"))

    for key, ne in n_map.items():
        if key not in o_map:
            diffs.append((_gap_key(ne), f"element invented: {key}"))
    return diffs


def _survey() -> tuple[dict, int, int]:
    """Round-trip the whole corpus. Returns (gaps, files_clean, files_total)."""
    loader = HDCLoader()
    gaps: dict = collections.defaultdict(list)
    clean = 0
    files = _corpus_files()
    for path in files:
        try:
            hero = loader.load_file(str(path))
            diffs = _diff_document(_parse(path.read_bytes()),
                                   _parse(hero_to_bytes(hero)))
        except Exception as exc:  # noqa: BLE001 — a load failure is a gap too
            gaps[f"!load|{type(exc).__name__}"].append(f"{path.name}: {exc}")
            continue
        if not diffs:
            clean += 1
            continue
        for key, detail in diffs:
            gaps[key].append(f"{path.name}: {detail}")
    return gaps, clean, len(files)


@pytest.fixture(scope="module")
def survey():
    return _survey()


def test_export_states_everything_the_source_stated(survey):
    """No character may come back saying less than it said."""
    gaps, clean, total = survey
    known = _ledger()
    new = {k: v for k, v in gaps.items() if k not in known}
    if new:
        lines = [f"{len(new)} export gaps not in the ledger "
                 f"({clean}/{total} characters round-trip clean):"]
        for key, hits in sorted(new.items(), key=lambda kv: -len(kv[1]))[:20]:
            lines.append(f"  {key}  ({len(hits)} occurrences)")
            lines.append(f"      e.g. {hits[0]}")
        pytest.fail("\n".join(lines))


def test_export_ledger_is_not_stale(survey):
    """A ledger entry that no longer reproduces is a free win — delete it."""
    gaps, _, _ = survey
    fixed = sorted(_ledger() - set(gaps))
    if fixed:
        pytest.fail(
            f"{len(fixed)} ledger entries no longer reproduce. Remove them "
            f"from {LEDGER_PATH.name} in the commit that fixed them:\n  "
            + "\n  ".join(fixed))
