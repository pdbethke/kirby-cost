"""Tests for the ported CONTACT (Perk) and BUMP_OF_DIRECTION (Talent) classes.

Verifies both register (not _FallbackObject) and that their cost matches the
Java rules (CONTACT 2 levels with the USEFUL adder = 3, BUMP_OF_DIRECTION = 3
fixed), on a temporary copy of PowerLad that has been given one of each.
"""
import pytest
from tests.own_copy import own_copy

import kirby_cost.objects._registry_imports  # noqa: F401
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects.perks.contact import Contact
from kirby_cost.objects.talents.bump_of_direction import BumpOfDirection

_CONTACT = (
    '<CONTACT XMLID="CONTACT" ID="9000000000060" BASECOST="0.0" LEVELS="2" '
    'ALIAS="Contact" POSITION="0" MULTIPLIER="1.0" NAME="Probe Contact" INPUT="Probe Contact">'
    '<ADDER XMLID="USEFUL" ID="9000000000061" BASECOST="1.0" LEVELS="0" '
    'ALIAS="Contact has" POSITION="-1" MULTIPLIER="1.0" OPTION="USEFUL" '
    'OPTIONID="USEFUL" OPTION_ALIAS="useful Skills or resources" SHOWALIAS="Yes" '
    'PRIVATE="No" REQUIRED="No" INCLUDEINBASE="No" DISPLAYINSTRING="Yes" GROUP="No" '
    'SELECTED="YES" /></CONTACT>')
_BUMP = ('<BUMP_OF_DIRECTION XMLID="BUMP_OF_DIRECTION" ID="9000000000062" BASECOST="3.0" '
         'LEVELS="0" ALIAS="Bump Of Direction" POSITION="0" MULTIPLIER="1.0" />')


@pytest.fixture
def hero(tmp_path):
    return HDCLoader().load_file(own_copy(
        tmp_path, section_xml=[("PERKS", _CONTACT), ("TALENTS", _BUMP)]))


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


def test_contact_cost_with_the_useful_adder(hero):
    contacts = [p for p in hero.perks if p.xmlid == "CONTACT"]
    assert contacts, "expected a CONTACT perk on the copy"
    # 2 levels * 1 + USEFUL adder (1) = 3
    assert abs(contacts[0].total_cost - 3.0) < 0.01


def test_bump_of_direction_cost_is_fixed(hero):
    bumps = [t for t in hero.talents if t.xmlid == "BUMP_OF_DIRECTION"]
    assert bumps, "expected a BUMP_OF_DIRECTION talent on the copy"
    assert abs(bumps[0].total_cost - 3.0) < 0.01
