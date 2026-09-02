"""The export-fidelity survey, shared by the two round trips it grades.

``test_export_fidelity`` asks whether an ``.hdc`` written back out says
everything the source said. ``test_build_doc_fidelity`` asks the same question
of the BUILD DOC, by sending the hero through ``to_build_json`` /
``build_from_json`` before writing it out. The comparison is identical; only
the middle hop differs, so it lives here once rather than being reimplemented
slightly differently in the second file.

Splitting this out was itself a finding. The build doc had exactly one gate —
``test_ose_json_roundtrip_is_lossless`` — and despite the name it compared the
summed ``real_cost`` and nothing else. Every field the doc has been caught
dropping (TEXT, NOTES, a power's NAME, a modifier's ALIAS, AFFECTS_PRIMARY /
AFFECTS_TOTAL) is COST-NEUTRAL, so a cost gate could never have seen any of
them. The .hdc path had the attribute-level property all along; the doc path
just was not held to it.
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

FIXTURES = Path(__file__).parent / "fixtures"

no_corpus = pytest.mark.skipif(
    corpus_root() is None,
    reason="no character corpus configured (set KIRBY_COST_CORPUS)",
)


def ledger(path: Path) -> set[str]:
    """Every key a ledger accounts for — defects and HD's own normalising."""
    if not path.exists():
        return set()
    doc = json.loads(path.read_text())
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


def survey(transform=None) -> tuple[dict, int, int]:
    """Round-trip the whole corpus. Returns (gaps, files_clean, files_total).

    ``transform`` is the middle hop: a callable taking the loaded hero and
    returning the hero to write out. ``None`` writes the loaded hero straight
    back, which is the .hdc round trip.
    """
    loader = HDCLoader()
    gaps: dict = collections.defaultdict(list)
    clean = 0
    files = _corpus_files()
    for path in files:
        try:
            hero = loader.load_file(str(path))
            if transform is not None:
                hero = transform(hero)
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
