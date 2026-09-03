"""The front door and the back door — one build, several shapes.

    hero.export(format="hdc")    -> bytes
    hero.export(format="json")   -> dict
    load_build(source, format="json") -> LoadedHero

**JSON here is a transport encoding of the HDC element tree, not a second
serializer.** That distinction is the whole design, and it is a repair.

The build doc used to be a hand-written subset in both directions: a list of
``if getattr(...)`` lines on the way out, and three lookup tables (``_ATTR``,
``_BOOL``, ``_TYPED_ATTR``) on the way in. Meanwhile the XML side wrote from
DECLARED descriptors (``XML_ATTRS`` / ``xml_schema()``), so an attribute added
to a class appeared in the .hdc automatically and in the doc only if somebody
remembered. Nobody remembered five times running: TEXT, NOTES, a power's NAME,
a modifier's ALIAS (HD's "Only With Tail" — the descriptor that makes a
limitation a limitation), and AFFECTS_PRIMARY / AFFECTS_TOTAL. Every one of
them is cost-neutral, and the doc's only gate compared summed cost, so the
losses were invisible until each was found by hand, downstream, in the
database.

Measured before this module existed: **0 of 794 corpus characters** survived
``.hdc -> hero -> doc -> hero -> .hdc`` intact — 609 element kinds dropped
(59,099 NOTES elements, 3,055 FOCUS modifiers, whole adder families) and 5,014
attribute keys churned.

So JSON does not get its own opinion about which fields exist. It encodes the
element tree the .hdc writer already produces — ``{tag, attrs, children,
text}`` — and decodes back to the same shape. Completeness is STRUCTURAL: there
is no field list to drift, because there is no second field list. Anything the
XML writer learns to say, JSON says the same day.
"""
from __future__ import annotations

from typing import Any, Callable

from kirby_cost.io.hdc_loader import BuildNode, HDCLoader, LoadedHero
from kirby_cost.io.hdc_writer import hero_to_bytes, hero_to_element


class UnknownFormat(ValueError):
    """No door of that name. Names the ones there are, because a typo here
    would otherwise read as 'this build cannot be exported'."""


_EXPORTERS: dict[str, Callable[[Any], Any]] = {}
_IMPORTERS: dict[str, Callable[[Any], LoadedHero]] = {}


def export_format(name: str):
    """Register a back door. Additive: a new shape is a registration, never an
    edit to a dispatcher that has to be taught about it."""
    def register(fn):
        _EXPORTERS[name] = fn
        return fn
    return register


def import_format(name: str):
    """Register a front door, symmetric with its back door."""
    def register(fn):
        _IMPORTERS[name] = fn
        return fn
    return register


def _known(registry: dict) -> str:
    return ", ".join(sorted(registry)) or "none registered"


# ── the encoding ───────────────────────────────────────────────────────────

def element_to_json(element) -> dict[str, Any]:
    """An element tree as plain JSON-able data.

    Deliberately dumb: tag, attributes verbatim as the strings the document
    holds, children in document order, and text when there is any. No key is
    renamed and no value is coerced, so nothing here can decide a field is
    uninteresting — the decision about what an object states was already made
    once, by ``write_xml_attrs``, from the declared schema.
    """
    node: dict[str, Any] = {"tag": element.tag, "attrs": dict(element.attrib)}
    children = [element_to_json(child) for child in element
                if isinstance(child.tag, str)]
    if children:
        node["children"] = children
    text = (element.text or "").strip()
    if text:
        node["text"] = text
    return node


def json_to_element(node: Any) -> BuildNode:
    """The inverse. Returns a ``BuildNode``, the loader's element-compatible
    adapter, so the decoded tree goes through the SAME construction core an
    .hdc does rather than a parallel one."""
    if not isinstance(node, dict) or "tag" not in node:
        raise ValueError(f"not an encoded element: {node!r}")
    attrs = {str(k): str(v) for k, v in (node.get("attrs") or {}).items()}
    return BuildNode(
        str(node["tag"]),
        attrs,
        [json_to_element(child) for child in (node.get("children") or [])],
        text=node.get("text"),
        # These attributes ARE what the document stated, in its order — that is
        # what makes this encoding faithful rather than a curated subset, and
        # the loader has to be told so or the rebuild writes back a different
        # set. See BuildNode.stated.
        stated=tuple(attrs),
    )


# ── the doors ──────────────────────────────────────────────────────────────

@export_format("hdc")
def _export_hdc(hero) -> bytes:
    return hero_to_bytes(hero)


@export_format("json")
def _export_json(hero) -> dict[str, Any]:
    """The document, plus the document facts that live outside its tree.

    ``source_encoding`` is the one that bites: HD writes UTF-16 and some files
    are UTF-8, ``hero_to_bytes`` defaults to the encoding the character was
    READ from, and a hero rebuilt from JSON has not read anything. Without it
    two corpus characters came back XML-identical and byte-different — the
    same document in the wrong encoding, which is still not the file HD
    wrote.
    """
    doc: dict[str, Any] = {"document": element_to_json(hero_to_element(hero))}
    encoding = getattr(hero, "source_encoding", "")
    if encoding:
        doc["encoding"] = encoding
    return doc


@import_format("hdc")
def _import_hdc(source) -> LoadedHero:
    return HDCLoader().load_file(str(source))


@import_format("json")
def _import_json(source) -> LoadedHero:
    """Accepts the envelope, or a bare encoded document for hand-authored
    input — a document with no envelope simply states no encoding."""
    if isinstance(source, dict) and "document" in source:
        root, encoding = source["document"], source.get("encoding", "")
    else:
        root, encoding = source, ""
    hero = HDCLoader()._build_hero_from_root(json_to_element(root))
    if encoding:
        hero.source_encoding = encoding
    return hero


def export_build(hero, *, format: str = "hdc"):
    """The back door. ``LoadedHero.export`` is the method form of this."""
    try:
        exporter = _EXPORTERS[format]
    except KeyError:
        raise UnknownFormat(
            f"no exporter for {format!r}; have: {_known(_EXPORTERS)}") from None
    return exporter(hero)


def load_build(source, *, format: str = "hdc") -> LoadedHero:
    """The front door. ``source`` is a path for 'hdc', decoded data for 'json'."""
    try:
        importer = _IMPORTERS[format]
    except KeyError:
        raise UnknownFormat(
            f"no importer for {format!r}; have: {_known(_IMPORTERS)}") from None
    return importer(source)
