"""A framework knows its own slots, not merely the slots knowing their parent.

`List.objects` is Java's `getObjects()` and several rules read it. The loader
linked children upward (`child.parent = framework`) but never populated the
framework's own list, so every framework in the corpus reported zero slots and
any rule that asks the container about its contents silently saw an empty pool.

`Charges.parentUsesEND()` is the rule that exposes it. A Multipower reserve does
not itself use END — its slots do — so Java asks them
(`Charges.java:450-470`)::

    if (parent instanceof com.hero.objects.List) {
        for (GenericObject o : list.getObjects())
            if (childUsesEND(o)) return true;
        return false;
    }

With no objects to iterate the engine concluded the reserve uses no END, which
sets `max = 0` and clamps CHARGES to nothing. A corpus
villain's Blaster Rifle was a 30-point reserve whose CHARGES carries a +0.25 advantage:
the oracle priced a 30-point reserve with that advantage 30 x 1.25 = 37.5,
round-half-down to 37, and the engine returned the bare 30. The test below runs
the same rule on a temporary copy of PowerLad, whose own Multipower is a 45-point
reserve: 45 x 1.25 = 56.25, so 56 where the clamp bug gave 45.
"""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects.list import List as HeroList

# +1/4 Charges (32), on the reserve itself, as HD writes it.
_CHARGES_32 = ('<MODIFIER XMLID="CHARGES" ID="9000000000010" BASECOST="0.25" LEVELS="0" '
               'ALIAS="Charges" POSITION="-1" MULTIPLIER="1.0" OPTION="THIRTYTWO" '
               'OPTIONID="THIRTYTWO" OPTION_ALIAS="32" PRIVATE="No" FORCEALLOW="No" />')


@pytest.fixture
def hero(tmp_path):
    """PowerLad with +1/4 Charges added to his Multipower reserve."""
    from lxml import etree
    from tests.corpus import require_authored_hdc
    root = etree.parse(str(require_authored_hdc("PowerLad"))).getroot()
    root.find(".//MULTIPOWER").append(etree.fromstring(_CHARGES_32))
    path = tmp_path / "PowerLad-charges.hdc"
    path.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
    return HDCLoader().load_file(str(path))


def _reserve(hero):
    for p in hero.powers:
        if type(p).__name__ == "Multipower":
            return p
    pytest.fail("no Multipower loaded")


def test_the_framework_holds_the_slots_that_point_at_it(hero):
    reserve = _reserve(hero)
    linked = [p for p in hero.powers if getattr(p, "parent", None) is reserve]

    assert linked, "slots must link upward for this test to mean anything"
    assert isinstance(reserve, HeroList)
    assert len(reserve.objects) == len(linked)
    assert {id(o) for o in reserve.objects} == {id(o) for o in linked}


def test_a_reserve_uses_end_when_its_slots_do(hero):
    reserve = _reserve(hero)
    charges = next(m for m in reserve.assigned_modifiers if m.xmlid == "CHARGES")

    # A slot beneath this list reports computed uses_end False -- the list's
    # own CHARGES reaches it through the parent walk, exactly as Java's
    # usesEND() would say. The question HD actually asks for pricing the
    # list's Charges is childUsesEND (Charges.java:76-99): strip CHARGES,
    # detach the slot, then ask -- and THAT is true here.
    assert not any(o.uses_end for o in reserve.objects)
    assert any(charges._child_uses_end(o) for o in reserve.objects)
    assert charges._parent_uses_end() is True


def test_the_charges_advantage_is_no_longer_clamped_away(hero):
    charges = next(m for m in _reserve(hero).assigned_modifiers if m.xmlid == "CHARGES")
    assert charges.total_value == 0.25


def test_the_reserve_costs_its_charges_advantage(hero):
    """45 x 1.25 = 56.25 -> 56."""
    assert _reserve(hero).real_cost == 56


def test_the_character_total_carries_the_advantage(hero):
    """PowerLad is 399.5 without the Charges; the reserve gains 56 - 45."""
    assert hero.total_points == 399.5 + 11
