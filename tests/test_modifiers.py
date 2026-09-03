"""One walk for "does this purchase carry that modifier".

Three copies of this question existed and disagreed. The one that bit was
kirby-combat's ``_has_modifier`` — a flat scan of ``assigned_modifiers`` doing
neither recursion nor inheritance, behind ARMORPIERCING, PENETRATING,
HARDENED, IMPENETRABLE and DOESBODY.
"""
from __future__ import annotations

from kirby_cost.io.formats import load_build
from kirby_cost.model.modifiers import (
    find_modifier, has_modifier, modifier_levels,
)


class _Mod:
    def __init__(self, xmlid, levels=0, private=False):
        self.xmlid, self.levels, self.private = xmlid, levels, private


class _Purchase:
    """Enough of a purchase for the walk: its own modifiers, and a parent."""

    def __init__(self, xmlid="STR", mods=(), parent=None):
        self.xmlid = xmlid
        self.assigned_modifiers = list(mods)
        self.parent = parent
        self.main_power = None


def test_a_purchases_own_modifier_is_found():
    p = _Purchase(mods=[_Mod("ARMORPIERCING", levels=2)])
    assert has_modifier(p, "ARMORPIERCING")
    assert modifier_levels(p, "ARMORPIERCING") == 2


def test_a_missing_modifier_reads_zero_not_an_error():
    assert has_modifier(_Purchase(), "PENETRATING") is False
    assert modifier_levels(_Purchase(), "PENETRATING") == 0


def test_an_enclosing_purchases_modifier_binds_the_slot():
    """HD prints a pool's limitations on each slot, and Java's
    getAllAssignedModifiers merges an object's modifiers with its parent's."""
    pool = _Purchase("MULTIPOWER", mods=[_Mod("ARMORPIERCING", levels=1)])
    slot = _Purchase("BLAST", parent=pool)
    assert has_modifier(slot, "ARMORPIERCING")
    assert modifier_levels(slot, "ARMORPIERCING") == 1


def test_an_enclosing_purchases_PRIVATE_modifier_does_not():
    """``List.separatePrivateMods`` moves those off the shared list precisely
    because they price the pool and do not reach its slots."""
    pool = _Purchase("MULTIPOWER", mods=[_Mod("ARMORPIERCING", private=True)])
    assert has_modifier(_Purchase("BLAST", parent=pool), "ARMORPIERCING") is False


def test_inheritance_can_be_switched_off():
    pool = _Purchase("MULTIPOWER", mods=[_Mod("OIHID")])
    slot = _Purchase("STR", parent=pool)
    assert has_modifier(slot, "OIHID") is True
    assert has_modifier(slot, "OIHID", inherited=False) is False


def test_the_walk_reaches_a_modifier_inside_a_container():
    """A container holds its contents in ``objects``; a flat scan stops at it.
    This is ``GenericObject.find_object_by_id``'s own rule, not a new one."""
    class _Container:
        xmlid = "LIST"
        def __init__(self, inner):
            self.objects = inner
            self.powers = []

    inner = _Mod("RESISTANT")
    p = _Purchase(mods=[_Container([inner])])
    assert find_modifier(p, "RESISTANT") is inner


def test_ravels_pool_binds_its_slot_on_the_real_document():
    """The .hdc path is the one that rebuilds framework membership, so this is
    where inheritance is observable on real data: the slot carries no OIHID of
    its own, and the pool does."""
    hero = load_build("tests/fixtures/authored/Ravel.hdc", format="hdc")
    slot = next(p for p in hero.powers
                if (p.name or "").strip() == "Reinforced String")
    assert has_modifier(slot, "OIHID", inherited=False) is False
    assert has_modifier(slot, "OIHID") is True
