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
(the HD comparison harness, 2026-08-17) moved 8 of 655 fixtures and exposed this.

Resolution follows HD: `builtIn.X.hdt` names one of the templates shipped with
the application, which live together in one directory, so it resolves to the
file of that name beside the configured template.
"""
import os
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.own_copy import vehicle_copy

TEMPLATE_DIR = Path(os.environ["KIRBY_COST_HDT"]).parent if os.environ.get(
    "KIRBY_COST_HDT") else None

pytestmark = pytest.mark.skipif(
    TEMPLATE_DIR is None or not (TEMPLATE_DIR / "Vehicle6E.hdt").is_file(),
    reason="template directory absent",
)


@pytest.fixture
def vehicle(tmp_path):
    return HDCLoader().load_file(vehicle_copy(tmp_path))


def test_a_vehicle_resolves_its_own_template(vehicle):
    """SIZE exists only in Vehicle6E, so resolving it is observable."""
    assert vehicle.template_name == "builtIn.Vehicle6E.hdt"
    assert "SIZE" in [c.xmlid for c in vehicle.characteristics]


def test_the_vehicle_movement_powers_do_not_use_end(vehicle):
    """Vehicle6E states USESEND="No" on FLIGHT where Main6E says "Yes"."""
    flight = next(p for p in vehicle.powers if p.xmlid == "FLIGHT")

    assert flight.uses_end is False


def test_the_vehicle_prices_size_at_the_vehicle_rate(vehicle):
    """Costed against Vehicle6E, SIZE 4 at 5/level costs 20."""
    size = next(c for c in vehicle.characteristics if c.xmlid == "SIZE")
    assert size.real_cost == 4 * 5.0


def test_the_vehicle_total_is_what_hd_says(vehicle):
    """The whole vehicle against HD's own answer for this file (the headless
    oracle, 2026-11-24): 377.5. Vehicle6E REMOVEs CON, INT, EGO, PRE, OMCV,
    DMCV, REC, END and STUN, so the 45 points this character had in them, and
    the 7 in its PRE power, are not a vehicle's. This test used to compare
    against the same character on Superheroic6E and expected only SIZE to
    differ, which was true only while no template's REMOVE was honoured
    (engine 429.5, HD 377.5)."""
    assert vehicle.total_points == 377.5
    assert not {"CON", "INT", "EGO", "PRE", "OMCV", "DMCV", "REC", "END",
                "STUN"} & {c.xmlid for c in vehicle.characteristics}


def test_a_main6e_character_is_unaffected():
    """A character on a non-vehicle template never moves; this guards that."""
    from tests.corpus import require_authored_hdc
    hero = HDCLoader().load_file(str(require_authored_hdc("PowerLad")))
    assert hero.template_name == "builtIn.Superheroic6E.hdt"
    assert hero.total_points == 399.5
    flight = next((p for p in hero.powers if p.xmlid == "FLIGHT"), None)
    if flight is not None:
        assert flight.orig_uses_end is True
        assert flight.uses_end is False
