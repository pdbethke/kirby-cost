from tests.corpus import hero_docs_root
from pathlib import Path
import pytest
from kirby_cost.io.hdc_loader import HDCLoader

FIREWING = (hero_docs_root() or Path("/nonexistent")) / "Old School Enemies/Old School Enemies HD Files/Firewing.hdc"

def _total(h):
    return sum((getattr(o, "real_cost", 0) or 0)
               for attr in ("characteristics", "skills", "perks", "talents", "powers")
               for o in getattr(h, attr, []))

@pytest.mark.skipif(not FIREWING.exists(), reason="Firewing HDC not present")
def test_load_file_firewing_total():
    hero = HDCLoader().load_file(str(FIREWING))
    assert round(_total(hero)) == 758


@pytest.mark.skipif(not FIREWING.exists(), reason="Firewing HDC not present")
def test_build_hero_from_root_accepts_in_memory_root():
    from lxml import etree
    raw = FIREWING.read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8")
    if text.startswith("<?xml"):
        text = text[text.index("?>") + 2:].lstrip()
    root = etree.fromstring(text.encode("utf-8"))
    hero = HDCLoader()._build_hero_from_root(root)
    assert round(_total(hero)) == 758
