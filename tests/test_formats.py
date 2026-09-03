"""The front door and the back door.

The corpus gate (``test_build_doc_fidelity``) proves the property at scale but
skips without ``KIRBY_COST_CORPUS``, which is everyone who is not the
maintainer. These run on the three authored characters that ship in the repo.
"""
from __future__ import annotations

import pytest

from kirby_cost.io.formats import (
    UnknownFormat, element_to_json, json_to_element, load_build,
)

AUTHORED = ["Ravel", "Bokor", "PowerLad"]


def _hero(name):
    return load_build(f"tests/fixtures/authored/{name}.hdc", format="hdc")


@pytest.mark.parametrize("name", AUTHORED)
def test_a_character_survives_the_json_door_byte_for_byte(name):
    """.hdc -> hero -> json -> hero -> .hdc, and the bytes are the same bytes.

    Byte equality rather than an XML comparison: these three carry no embedded
    template block, so there is no whitespace the writer has to re-indent, and
    anything weaker would not have caught the defects this door was built to
    close.
    """
    hero = _hero(name)
    again = load_build(hero.export(format="json"), format="json")
    assert again.export(format="hdc") == hero.export(format="hdc")


def test_the_encoding_travels_with_the_document():
    """``hero_to_bytes`` defaults to the encoding the character was READ from,
    and a hero rebuilt from JSON has read nothing — so the envelope states it.
    Without this two corpus characters came back XML-identical and
    byte-different: the same document in the wrong encoding."""
    hero = _hero("Ravel")
    doc = hero.export(format="json")
    assert doc["encoding"] == hero.source_encoding
    assert load_build(doc, format="json").source_encoding == hero.source_encoding


def test_a_bare_document_is_accepted_without_an_envelope():
    """Hand-authored input has no encoding to state."""
    doc = _hero("Ravel").export(format="json")
    assert load_build(doc["document"], format="json").name == _hero("Ravel").name


def test_the_encoding_is_bijective():
    """The point of the whole design: JSON is a transport encoding of the
    element tree, not a second serializer with its own opinion about which
    fields matter. Encode, decode, encode — nothing may move."""
    from kirby_cost.io.hdc_writer import hero_to_element

    tree = hero_to_element(_hero("Ravel"))
    once = element_to_json(tree)
    # element_to_json over the DECODED node, not the lxml tree: BuildNode
    # answers the same element API, which is what makes the trip checkable
    # from either end.
    twice = element_to_json(json_to_element(once))
    assert twice == once


def test_statedness_survives_the_trip():
    """A decoded node reports the attributes the document stated, in order.

    Left unsaid, the rebuild lost every explicitly-stated empty value (NAME="")
    and invented a dozen defaults per element — LVLCOST, SHOWALIAS, QUANTITY.
    """
    node = json_to_element({"tag": "POWER",
                            "attrs": {"XMLID": "STR", "NAME": "", "LEVELS": "20"}})
    assert node.keys() == ("XMLID", "NAME", "LEVELS")


def test_a_node_that_names_no_source_states_nothing():
    """The legacy build doc builds BuildNodes whose keys are that emitter's
    curated field list, NOT the source's statement. Treating those as stated
    would freeze template-derived values into the file as though the character
    had declared them — the MINCOST defect that made HD recost two of Ravel's
    skills 3 -> 2. Absent ``stated``, keys() is empty, exactly as before."""
    from kirby_cost.io.hdc_loader import BuildNode

    assert BuildNode("POWER", {"XMLID": "STR"}).keys() == ()


def test_an_unknown_format_says_which_ones_exist():
    with pytest.raises(UnknownFormat) as exc:
        load_build("x", format="yaml")
    assert "hdc" in str(exc.value) and "json" in str(exc.value)

    with pytest.raises(UnknownFormat):
        _hero("Ravel").export(format="yaml")


def test_a_preserved_element_re_materialises_for_the_writer():
    """``embedded_template`` is kept VERBATIM from the source, so on the json
    path it is a BuildNode and lxml's append rejects it outright — 15 corpus
    characters failed to write at all with a bare TypeError."""
    from kirby_cost.io.hdc_loader import BuildNode
    from kirby_cost.io.hdc_writer import _as_lxml

    node = BuildNode("TEMPLATE", {"NAME": "Main6E"},
                     [BuildNode("CHILD", {"A": "1"})], text="x")
    element = _as_lxml(node)
    assert element.tag == "TEMPLATE"
    assert element.get("NAME") == "Main6E"
    assert [c.tag for c in element] == ["CHILD"]
