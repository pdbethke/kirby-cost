"""Write a character back out as a HERO Designer ``.hdc`` document.

The fourth leg of the round trip: ``HDCLoader`` reads an HDC into a class
graph, the engine costs it, a caller edits it, and this puts it back on disk
as a file HERO Designer will open.

**This is a projection of the object, not an assembly of a file.** The
character object is meant to be the full shape of the HDC in class form, so
everything here reads ``LoadedHero`` and its objects and nothing else. It has
no storage, no schema and no knowledge of any consumer's database — a
relational projection is built FROM this shape, downstream, never the reverse.
That direction is the point: the previous exporter lived in
``kirby_cost/database/character_exporter.py`` and was deleted wholesale in
1da1b54, "the engine has no database". It was never part of the ORM; it merely
sat beside one, and went out with it. Nothing here may acquire that dependency
again — ``tests/test_pure_code.py`` enforces the boundary.

Objects serialize themselves (``SerializationMixin.get_save_xml``), including
their adders, modifiers, selected option, ``PARENTID`` and ``ULTRA_SLOT``. This
module's whole job is the envelope: the ``CHARACTER`` element, the metadata HD
keeps as attributes, and the section elements in the order HD writes them.

Two rules it exists to keep:

**Every section the loader reads is written.** The only assembler this repo had
between 1da1b54 and now was a helper inside ``tests/test_metadata_roundtrip.py``
that wrote six sections and no ``MARTIALARTS``, so a martial artist round-tripped
into someone who had forgotten their art.

**A failure to write an object raises.** That same helper wrapped each object in
``except Exception: pass``, which converts a serialization bug into a silently
shorter character — the worst possible outcome for a format whose whole purpose
is to be reloaded.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Iterable

from lxml import etree


class HDCWriteError(RuntimeError):
    """An object could not be written. Never swallowed: a dropped object is a
    character that silently lost part of its build."""


#: Top-level children, in the order HERO Designer itself writes them, so a
#: diff between our output and an HD re-save stays readable. Sections are
#: always emitted, empty ones included — HD writes an empty ``<EQUIPMENT/>``
#: too, and a missing section and an empty one are not the same statement.
SECTION_ORDER = (
    "BASIC_CONFIGURATION",
    "CHARACTER_INFO",
    "CHARACTERISTICS",
    "SKILLS",
    "PERKS",
    "TALENTS",
    "MARTIALARTS",
    "POWERS",
    "DISADVANTAGES",
    "EQUIPMENT",
)

#: section tag -> the LoadedHero attribute holding its objects. Sections not
#: listed here carry attributes or text rather than objects.
_OBJECT_SECTIONS = {
    "CHARACTERISTICS": "characteristics",
    "SKILLS": "skills",
    "PERKS": "perks",
    "TALENTS": "talents",
    "MARTIALARTS": "martial_arts",
    "POWERS": "powers",
    "DISADVANTAGES": "complications",
    "EQUIPMENT": "equipment",
}

#: CHARACTER_INFO attributes -> the attribute on the hero.
_INFO_ATTRS = (
    ("CHARACTER_NAME", "name"),
    ("ALTERNATE_IDENTITIES", "alternate_identities"),
    ("PLAYER_NAME", "player_name"),
    ("HEIGHT", "height"),
    ("WEIGHT", "weight"),
    ("HAIR_COLOR", "hair_color"),
    ("EYE_COLOR", "eye_color"),
    ("CAMPAIGN_NAME", "campaign_name"),
    ("GENRE", "genre"),
    ("GM", "gm"),
)

#: CHARACTER_INFO child elements carrying prose. Written in HD's order, and
#: always written: HD emits the empty ones, and a character whose background
#: is deliberately blank should not be indistinguishable from one that never
#: had the field.
TEXT_FIELDS = (
    "BACKGROUND", "PERSONALITY", "QUOTE", "TACTICS", "CAMPAIGN_USE",
    "APPEARANCE", "NOTES1", "NOTES2", "NOTES3", "NOTES4", "NOTES5",
)

_DEFAULT_ENCODING = "utf-16"


def _element_for(obj: Any, section: str) -> etree._Element:
    """One object's element, or raise saying which object refused."""
    ident = getattr(obj, "xmlid", None) or type(obj).__name__
    name = (getattr(obj, "_name", "") or getattr(obj, "name", "") or "").strip()
    label = f"{section} {ident}" + (f" ({name})" if name else "")
    try:
        element = obj.save_xml()
    except Exception as exc:  # noqa: BLE001 — re-raised with the object named
        raise HDCWriteError(f"{label} could not be written: {exc}") from exc
    if element is None:
        raise HDCWriteError(f"{label} produced no XML")
    return element


def _append_objects(parent: etree._Element, objects: Iterable[Any],
                    section: str) -> None:
    for obj in objects or ():
        parent.append(_element_for(obj, section))


def hero_to_element(hero: Any) -> etree._Element:
    """Project a character onto a ``CHARACTER`` element.

    Every value comes from the object. Where the document states something the
    object cannot hold, that is a hole in the object model to be closed there —
    ``version``, ``export_template`` and ``source_encoding`` were exactly that,
    and are fields on ``LoadedHero`` for this reason rather than constants here.
    """
    root = etree.Element("CHARACTER")
    root.set("version", getattr(hero, "version", "") or "6.0")
    # A character is costed against the template it DECLARES; writing a
    # different name would recost it on reload.
    root.set("TEMPLATE", getattr(hero, "template_name", "") or "")

    basic = etree.SubElement(root, "BASIC_CONFIGURATION")
    basic.set("BASE_POINTS", str(hero.base_points))
    basic.set("DISAD_POINTS", str(hero.disad_points))
    basic.set("EXPERIENCE", str(hero.experience))
    # Only when the document named a ruleset here. This was `"Default"`
    # unconditionally, which stated the attribute on 133 characters whose files
    # do not carry it — and would have overwritten any other campaign's name.
    if getattr(hero, "rules_name", ""):
        basic.set("RULES", hero.rules_name)
    if getattr(hero, "export_template", ""):
        basic.set("EXPORT_TEMPLATE", hero.export_template)

    info = etree.SubElement(root, "CHARACTER_INFO")
    for attr, field in _INFO_ATTRS:
        value = getattr(hero, field, "")
        info.set(attr, "" if value is None else str(value))
    for field in TEXT_FIELDS:
        child = etree.SubElement(info, field)
        text = getattr(hero, field.lower(), "") or ""
        if text:
            child.text = text

    for section in SECTION_ORDER:
        if section not in _OBJECT_SECTIONS:
            continue
        element = etree.SubElement(root, section)
        _append_objects(element, getattr(hero, _OBJECT_SECTIONS[section], []),
                        section)

    # The campaign ruleset, as the document stated it. This used to write a
    # RULES element carrying ONE attribute — the language-similarities flag,
    # the only one the engine reads — which is not a smaller version of the
    # block, it is a different ruleset: HD fills the other ~69 back in from its
    # own defaults on load, so a Heroic 6E character reloaded as a Standard
    # one. Where the object holds the block, it is written whole; where it does
    # not (a character built in Python, which never had one), the flag the
    # engine does model is still stated, as before.
    rules_attrs = dict(getattr(hero, "rules_attrs", {}) or {})
    rules = getattr(hero, "rules", None)
    if not rules_attrs and rules is not None and getattr(
            rules, "_language_similarities_used", False):
        rules_attrs = {"LANGUAGESIMILARITIESUSED": "Yes"}
    if rules_attrs:
        element = etree.SubElement(root, "RULES")
        for key, value in rules_attrs.items():
            element.set(key, value)

    # The character's own embedded template, after RULES as HD writes it.
    embedded = getattr(hero, "embedded_template", None)
    if embedded is not None:
        root.append(copy.deepcopy(embedded))

    if getattr(hero, "image_data", ""):
        image = etree.SubElement(root, "IMAGE")
        image.set("FILENAME", getattr(hero, "image_filename", "") or "")
        image.text = hero.image_data

    return root


def _space_before_self_close(body: str) -> str:
    """``<NOTES/>`` -> ``<NOTES />``, the way HD writes it.

    Tag- and quote-aware rather than a regex. Both halves are needed. An
    attribute value may legitimately contain "/>" -- NOTES and COMMENTS are
    free text a player typed -- so quotes have to be honoured; and quotes only
    delimit anything INSIDE a tag, so the scanner has to know where it is.
    Tracking quotes alone breaks on the first piece of quoted dialogue in a
    BACKGROUND: one character's quote ran the rest of his document as though
    it were one long attribute value, and 155 of his 156 empty tags came out
    unspaced.
    """
    out = []
    in_tag = False
    quote = ""
    for i, ch in enumerate(body):
        if quote:
            if ch == quote:
                quote = ""
        elif in_tag:
            if ch in "\"'":
                quote = ch
            elif ch == ">":
                in_tag = False
            elif (ch == "/" and body[i + 1:i + 2] == ">"
                    and not body[i - 1:i].isspace()):
                out.append(" ")
        elif ch == "<":
            in_tag = True
        out.append(ch)
    return "".join(out)


def hero_to_bytes(hero: Any, encoding: str | None = None) -> bytes:
    """The whole document, encoded as HD encodes it.

    Defaults to the encoding the character was READ from
    (``LoadedHero.source_encoding``), falling back to UTF-16, which is what
    HERO Designer writes. The declaration and CRLF line endings are written by
    hand rather than left to lxml, which quotes the declaration with
    apostrophes and separates lines with bare newlines — both legal XML, and
    both a gratuitous diff against every file HD has ever produced.

    One deliberate simplification: a UTF-16 file is written back little-endian
    with a BOM regardless of the byte order it arrived in. HD reads either.
    """
    enc = (encoding or getattr(hero, "source_encoding", "")
           or _DEFAULT_ENCODING).lower()
    root = hero_to_element(hero)
    # lxml self-closes an element whose text is None and writes <X></X> when
    # the text is "". HD never writes the pair form -- 156 self-closing tags
    # and no empty pairs in a typical character -- so an empty string here is
    # 1,600 bytes of spurious diff on one file. Nothing distinguishes the two
    # in the document: an empty NOTES means the same thing either way.
    for element in root.iter():
        if len(element) == 0 and not (element.text or "").strip():
            element.text = None
    body = etree.tostring(root, pretty_print=True, encoding="unicode")
    body = _space_before_self_close(body)
    body = body.replace("\r\n", "\n").replace("\n", "\r\n")
    label = "UTF-16" if enc.startswith("utf-16") else "UTF-8"
    return (f'<?xml version="1.0" encoding="{label}"?>\r\n'
            + body).encode(enc)


def write_hdc(hero: Any, path: str | os.PathLike, encoding: str | None = None) -> Path:
    """Write ``hero`` to ``path`` as an HDC file. Returns the path written."""
    target = Path(path)
    target.write_bytes(hero_to_bytes(hero, encoding))
    return target
