"""The CHARACTERISTICS section is driven by the template, not by the file.

Java never iterates the file's characteristic elements. It walks the hero's own
characteristic set — built from the loaded template — and pulls each one OUT of
the section by name (`Hero.java:2472-2481`)::

    Element chs = root.getChild("CHARACTERISTICS");
    for (GenericObject ch : characteristics) {        // the template's set
        Element chk = chs.getChild(ch.getXMLID());    // pull it out of the file
        if (chk != null) { ch.restoreFromSave(chk); ch.setPower(false); }
    }

So an element the template does not define is never read, and costs nothing.
The engine enumerated the file instead and costed whatever it found.

**The example that first exposed this has since changed sides.** `SIZE` was the
case: four corpus vehicles carry `<SIZE LEVELS="4">`, `Main6E.hdt` has no SIZE,
and the engine charged 15/level for it. That was read as "SIZE is undefined, so
drop it" — but SIZE *is* defined, by `Vehicle6E.hdt`, which is the template
those characters declare. The engine simply was not resolving it (and the Java
oracle was not either, which is why the fixtures agreed). With both fixed, a
vehicle loads SIZE and pays Vehicle6E's 5/level for it.

The rule survives its example. A characteristic the RESOLVED template does not
define is still never loaded, which is what the synthetic case below pins: the
same `<SIZE>` element on a character that declares no template resolves against
Main6E, which has no SIZE, and is dropped.
"""
from tests.corpus import corpus_root
import os
import textwrap
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.template.hdt_provider import HDTTemplateProvider

_ROOT = (corpus_root() or Path("/nonexistent"))
HOVERTANK = (_ROOT / "villains/CV1HDFiles/CV1 HD Files ƒ/ISTVATHA_V'HAN"
             / "V'HANIAN_HOVERTANK-CV1.hdc")

STANDARD_6E = [
    "STR", "DEX", "CON", "INT", "EGO", "PRE", "OCV", "DCV", "OMCV", "DMCV",
    "SPD", "PD", "ED", "REC", "END", "BODY", "STUN", "RUNNING", "SWIMMING",
    "LEAPING",
]

pytestmark = pytest.mark.skipif(
    not os.environ.get("KIRBY_COST_HDT"),
    reason="no HERO Designer template configured",
)


def _write_hdc(tmp_path, template_attr: str) -> str:
    """A character with a SIZE characteristic, with or without a template."""
    xml = textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-16"?>
        <CHARACTER version="6.0"{template_attr}>
          <CHARACTER_INFO CHARACTER_NAME="Probe" />
          <CHARACTERISTICS>
            <SIZE XMLID="SIZE" ID="1" BASECOST="0.0" LEVELS="4" ALIAS="Size"
                  POSITION="0" MULTIPLIER="1.0" />
            <STR XMLID="STR" ID="2" BASECOST="0.0" LEVELS="5" ALIAS="STR"
                 POSITION="1" MULTIPLIER="1.0" />
          </CHARACTERISTICS>
          <SKILLS /><PERKS /><TALENTS /><POWERS /><DISADVANTAGES />
        </CHARACTER>
        """
    )
    p = tmp_path / "probe.hdc"
    p.write_bytes(xml.encode("utf-16"))
    return str(p)


def test_the_premise_every_standard_characteristic_is_in_the_template():
    """Guards the gate: if one of these went missing, gating would gut a hero."""
    provider = HDTTemplateProvider()
    missing = [x for x in STANDARD_6E if provider.get_template_data(x) is None]
    assert missing == []


def test_a_characteristic_the_resolved_template_lacks_is_not_loaded(tmp_path):
    """Main6E has no SIZE, so a template-less character drops it."""
    hero = HDCLoader().load_file(_write_hdc(tmp_path, ""))

    loaded = [c.xmlid for c in hero.characteristics]
    assert "SIZE" not in loaded
    assert "STR" in loaded, "the gate must not drop what the template DOES define"


@pytest.mark.skipif(not HOVERTANK.exists(), reason="machine-bound HDC corpus absent")
def test_a_characteristic_the_resolved_template_defines_is_loaded():
    """The same element on a Vehicle6E character, which does define SIZE."""
    hero = HDCLoader().load_file(str(HOVERTANK))

    assert hero.template_name == "builtIn.Vehicle6E.hdt"
    size = next((c for c in hero.characteristics if c.xmlid == "SIZE"), None)
    assert size is not None
    assert size.level_cost == 5.0, "Vehicle6E prices SIZE at 5/level"
