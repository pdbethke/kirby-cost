"""Tests for the ported CONTACT (Perk) and BUMP_OF_DIRECTION (Talent) classes.

Verifies both register (not _FallbackObject) and, where the OSE fixtures are
available, that their cost matches the Java oracle (CONTACT=3 on Frizbe with
the USEFUL adder, BUMP_OF_DIRECTION=3 fixed on Gaussian).
"""
from tests.corpus import hero_docs_root
import os
import pytest

import kirby_cost.objects._registry_imports  # noqa: F401
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects.perks.contact import Contact
from kirby_cost.objects.talents.bump_of_direction import BumpOfDirection

OSE_DIR = (
    str(hero_docs_root() or "/nonexistent") + "/Old School Enemies/"
    "Old School Enemies HD Files"
)


def test_contact_registers():
    ld = HDCLoader()
    obj = ld._create_instance("CONTACT", "power")
    assert isinstance(obj, Contact)
    assert type(obj).__name__ == "Contact"


def test_bump_of_direction_registers():
    ld = HDCLoader()
    obj = ld._create_instance("BUMP_OF_DIRECTION", "power")
    assert isinstance(obj, BumpOfDirection)
    assert type(obj).__name__ == "BumpOfDirection"


def test_contact_roll_matches_java():
    # Java Contact.getRoll(): 0/2 levels -> 11-, 1 -> 8-, >2 -> 11+(levels-2)
    c = Contact()
    c._levels = 2
    assert c.roll == "11-"
    c._levels = 1
    assert c.roll == "8-"
    c._levels = 4
    assert c.roll == "13-"


@pytest.mark.skipif(not os.path.isdir(OSE_DIR), reason="OSE fixtures unavailable")
def test_contact_cost_on_frizbe():
    hero = HDCLoader().load_file(os.path.join(OSE_DIR, "Frizbe.hdc"))
    contacts = [p for p in hero.perks if p.xmlid == "CONTACT"]
    assert contacts, "expected a CONTACT perk on Frizbe"
    # 2 levels * 1 + USEFUL adder (1) = 3
    assert abs(contacts[0].total_cost - 3.0) < 0.01


@pytest.mark.skipif(not os.path.isdir(OSE_DIR), reason="OSE fixtures unavailable")
def test_bump_of_direction_cost_on_gaussian():
    hero = HDCLoader().load_file(os.path.join(OSE_DIR, "Gaussian.hdc"))
    bumps = [t for t in hero.talents if t.xmlid == "BUMP_OF_DIRECTION"]
    assert bumps, "expected a BUMP_OF_DIRECTION talent on Gaussian"
    assert abs(bumps[0].total_cost - 3.0) < 0.01
