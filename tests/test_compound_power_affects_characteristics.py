"""CompoundPower.affects_characteristics reads its parts' increases.

The port called Java's ``getDexIncrease()``-style getters, which the Python
objects never had (they expose ``dex_increase`` attributes), so asking any
compound with a part whether it affects characteristics raised
AttributeError. Ravel's "Wrap 'em and Nap 'em" (Entangle + ...) and Bokor's
compounds hit it through ``Power.summable``.

Java (CompoundPower.java:64-128) checks STR..Leaping on each
CharAffectingObject part -- not OCV/DCV/OMCV/DMCV or the custom slots.
"""
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects.powers.compound_power import CompoundPower

RAVEL = "tests/fixtures/authored/Ravel.hdc"
WRAP_AND_NAP = "1648349598295"


def _wrap_and_nap() -> CompoundPower:
    char = HDCLoader().load_file(RAVEL)
    return next(p for p in char.powers if str(p.id) == WRAP_AND_NAP)


def test_a_compound_without_characteristic_parts_does_not_affect_them() -> None:
    compound = _wrap_and_nap()
    assert compound.affects_characteristics() is False
    assert compound.summable is False


def test_a_part_raising_dex_makes_the_compound_affect_characteristics() -> None:
    compound = _wrap_and_nap()
    compound.powers[0].dex_increase = 3.0
    assert compound.affects_characteristics() is True


def test_ocv_alone_does_not_count_as_hd_does_not() -> None:
    compound = _wrap_and_nap()
    compound.powers[0].ocv_increase = 2.0
    assert compound.affects_characteristics() is False
