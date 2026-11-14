from tests.corpus import require_authored_hdc
import pytest
from kirby_cost.io.hdc_loader import HDCLoader

POWERLAD = require_authored_hdc("PowerLad")

def _total(h):
    return sum((getattr(o, "real_cost", 0) or 0)
               for attr in ("characteristics", "skills", "perks", "talents", "powers")
               for o in getattr(h, attr, []))

def test_load_file_powerlad_total():
    hero = HDCLoader().load_file(str(POWERLAD))
    assert round(_total(hero)) == 400


def test_build_hero_from_root_accepts_in_memory_root():
    from lxml import etree
    raw = POWERLAD.read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8")
    if text.startswith("<?xml"):
        text = text[text.index("?>") + 2:].lstrip()
    root = etree.fromstring(text.encode("utf-8"))
    hero = HDCLoader()._build_hero_from_root(root)
    assert round(_total(hero)) == 400
