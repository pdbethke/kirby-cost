"""A character is costed against the template it declares.

`<CHARACTER TEMPLATE="builtIn.Vehicle6E.hdt">` is not decoration: HD loads that
template and costs the character against it, and every specialised template is
a thin override layer over Main6E (`extends="builtIn.Main6E.hdt"`). Vehicle6E
restates FLIGHT as `USESEND="No"` and defines SIZE; Automaton6E prices EGO at
2/level; Computer6E defines PROGRAM, which Main6E does not.

The loader used to ignore the attribute and cost everything against whatever
single template the provider was configured with. A hand-rolled
`_apply_vehicle6e_overrides` patched a couple of the differences back in, which
its own docstring had already found to be half wrong.

**Why this went unnoticed for months:** the Java oracle had the same bug from
the other end. The headless fork could not resolve `builtIn.` names, so it
silently kept the Main6E bootstrap for every character, and the fixtures agreed
with an engine that also ignored the attribute. Fixing the oracle
(kirby-hd-oracle, 2026-08-17) moved 8 of 655 fixtures and exposed this.

Resolution follows HD: `builtIn.X.hdt` names one of the templates shipped with
the application, which live together in one directory, so it resolves to the
file of that name beside the configured template.
"""
from tests.corpus import corpus_root
import os
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

_ROOT = (corpus_root() or Path("/nonexistent"))
HOVERTANK = (_ROOT / "villains/CV1HDFiles/CV1 HD Files ƒ/ISTVATHA_V'HAN"
             / "V'HANIAN_HOVERTANK-CV1.hdc")
GRAVITAR = _ROOT / "villains/CV1HDFiles/CV1 HD Files ƒ/GRAVITAR-CV1.hdc"
TEMPLATE_DIR = Path(os.environ["KIRBY_COST_HDT"]).parent if os.environ.get(
    "KIRBY_COST_HDT") else None

pytestmark = pytest.mark.skipif(
    not HOVERTANK.exists() or TEMPLATE_DIR is None
    or not (TEMPLATE_DIR / "Vehicle6E.hdt").is_file(),
    reason="machine-bound HDC corpus or template directory absent",
)


def test_a_vehicle_resolves_its_own_template():
    """SIZE exists only in Vehicle6E, so resolving it is observable."""
    hero = HDCLoader().load_file(str(HOVERTANK))

    assert hero.template_name == "builtIn.Vehicle6E.hdt"
    assert "SIZE" in [c.xmlid for c in hero.characteristics]


def test_the_vehicle_movement_powers_do_not_use_end():
    """Vehicle6E states USESEND="No" on FLIGHT where Main6E says "Yes"."""
    hero = HDCLoader().load_file(str(HOVERTANK))
    flight = next(p for p in hero.powers if p.xmlid == "FLIGHT")

    assert flight.uses_end is False


def test_the_vehicle_total_matches_the_oracle():
    """237 under the old Main6E-for-everything oracle; 270 against Vehicle6E."""
    hero = HDCLoader().load_file(str(HOVERTANK))
    assert hero.total_points == 270.0


def test_a_main6e_character_is_unaffected():
    """647 of 655 corpus characters never move; this guards that."""
    hero = HDCLoader().load_file(str(GRAVITAR))
    assert hero.total_points == 1456.0
    flight = next((p for p in hero.powers if p.xmlid == "FLIGHT"), None)
    if flight is not None:
        assert flight.uses_end is True
