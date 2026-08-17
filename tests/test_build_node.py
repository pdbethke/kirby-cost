from tests.corpus import hero_docs_root
from pathlib import Path
import pytest
from lxml import etree
from kirby_cost.io.hdc_loader import HDCLoader, BuildNode

FIREWING = (hero_docs_root() or Path("/nonexistent")) / "Old School Enemies/Old School Enemies HD Files/Firewing.hdc"

def _total(h):
    return sum((getattr(o, "real_cost", 0) or 0)
               for attr in ("characteristics", "skills", "perks", "talents", "powers")
               for o in getattr(h, attr, []))

def test_buildnode_implements_element_api():
    n = BuildNode("POWER", {"XMLID": "ENERGYBLAST", "LEVELS": "10"},
                  [BuildNode("MODIFIER", {"XMLID": "REDUCEDEND"})])
    assert n.tag == "POWER"
    assert n.get("XMLID") == "ENERGYBLAST"
    assert n.get("MISSING", "x") == "x"
    assert n.get("MISSING") is None
    assert n.findall("MODIFIER")[0].get("XMLID") == "REDUCEDEND"
    assert n.find("MODIFIER") is not None
    assert n.find("ADDER") is None
    assert len(list(n)) == 1

def _lxml_to_buildnode(el):
    return BuildNode(el.tag, dict(el.attrib),
                     [_lxml_to_buildnode(c) for c in el], el.text)

@pytest.mark.skipif(not FIREWING.exists(), reason="Firewing HDC not present")
def test_buildnode_root_reproduces_load_file():
    loader = HDCLoader()
    ref = loader.load_file(str(FIREWING))
    with open(FIREWING, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8")
    if text.startswith("<?xml"):
        text = text[text.index("?>") + 2:].lstrip()
    root = etree.fromstring(text.encode("utf-8"))
    via_bn = loader._build_hero_from_root(_lxml_to_buildnode(root))
    assert round(_total(via_bn)) == round(_total(ref)) == 758
