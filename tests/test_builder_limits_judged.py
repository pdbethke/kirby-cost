"""`judge` holds a build to its power level.

Character-workshop spec §5.2: a limit breach is reported exactly like an
illegal modifier -- ``Problem.Kind.OVER_LIMIT``, the purchase's HD ``ID`` (or
None for a whole-character measure), and what was measured against what.
Limits are maxima: a build AT a limit is inside it.
"""
from __future__ import annotations

import pytest

from kirby_cost.builder import (
    BOOK_DAMAGE_ADVANTAGES, DamageAdvantage, Kind, Limit, LimitError, Pick, Problem, Purchase, Template, apply, buy, judge,
    new_build,
)
from kirby_cost.io.build_json import build_from_json, to_build_json
from kirby_cost.io.formats import load_build
from kirby_cost.template.hdt_provider import HDTTemplateProvider
from tests.corpus import require_authored_hdc


@pytest.fixture(scope="module")
def provider():
    return HDTTemplateProvider()


def _authored(name):
    return to_build_json(load_build(str(require_authored_hdc(name)), format="hdc"))


def _empty(provider, template=Template.SUPERHEROIC):
    return new_build(template, template_provider=provider, name="Test NPC",
                     base_points=400, disad_points=0, experience=0)


def _with(doc, provider, *purchases):
    for p in purchases:
        doc = apply(doc, [buy(doc, p, template=provider)])
    return doc


def _power(xmlid, levels, *mods):
    return Purchase(Kind.POWER, xmlid, levels, "", None, (), tuple(mods))


def AP(n):
    return Limit(Limit.Kind.ACTIVE_POINTS, n, None, None)


# -- Active Points per power -------------------------------------------------

def test_a_power_over_the_cap_is_over_limit(provider):
    doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 15))   # 75 AP
    (p,) = judge(doc, limits=(AP(60),), template_provider=provider).problems
    assert p.kind is Problem.Kind.OVER_LIMIT
    assert p.hd_id == doc["powers"][0]["id"]
    assert p.xmlid is None
    assert p.detail == "Active Points 75; the limit is 60"


def test_a_power_at_the_cap_is_sound(provider):
    """Review Focus 5: a maximum is inclusive."""
    doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 12))   # 60 AP
    assert judge(doc, limits=(AP(60),), template_provider=provider).sound


def test_no_limits_is_stated_not_assumed(provider):
    doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 15))
    assert judge(doc, limits=(), template_provider=provider).sound


def test_limits_are_required(provider):
    doc = _empty(provider)
    with pytest.raises(TypeError):
        judge(doc, template_provider=provider)


# Ravel's purchases at 45 Active Points, by the Java oracle:
#   kirby-hd-oracle/hd6cli.sh kirby-cost/tests/fixtures/authored/Ravel.hdc
# lists these 14 plus the Multipower itself (GENERIC_OBJECT 1648348957819).
RAVEL_AT_45 = {
    "1649513585745", "1648349598295", "1787052005008", "1648350992201",
    "1669689380740", "1648491205792", "1648351359965", "1668208484281",
    "1669687349643", "1648490875918", "1668208377694", "1648352405583",
    "1669687876476", "1648349293079",
}
RAVEL_MULTIPOWER = "1648348957819"


def test_each_framework_slot_is_measured_and_the_framework_is_not(provider):
    """Review Focus 2: a pool is not a power. Each slot answers by its own
    id; the Multipower's own 45 is never reported."""
    verdict = judge(_authored("Ravel"), limits=(AP(44),),
                    template_provider=provider)
    over = {p.hd_id for p in verdict.problems
            if p.kind is Problem.Kind.OVER_LIMIT}
    assert over == RAVEL_AT_45
    assert RAVEL_MULTIPOWER not in over


def test_an_authored_character_at_his_largest_power_is_sound(provider):
    verdict = judge(_authored("Ravel"), limits=(AP(45),),
                    template_provider=provider)
    assert not [p for p in verdict.problems
                if p.kind is Problem.Kind.OVER_LIMIT]



# -- Characteristic maxima (OCV, DCV, SPD, ...) -------------------------------

def CH(xmlid, n):
    return Limit(Limit.Kind.CHARACTERISTIC_MAX, n, xmlid, None)


def _set(doc, xmlid, levels):
    from kirby_cost.builder import Replace
    (row,) = [c for c in doc["characteristics"] if c["xmlid"] == xmlid]
    return apply(doc, [Replace(row["id"], {**row, "levels": levels})])


def test_a_characteristic_over_its_maximum_is_over_limit(provider):
    doc = _set(_empty(provider), "SPD", 4)            # Superheroic base 2 + 4
    (p,) = judge(doc, limits=(CH("SPD", 5),), template_provider=provider).problems
    assert p.kind is Problem.Kind.OVER_LIMIT and p.hd_id is None
    assert p.detail == "SPD 6; the limit is 5"


def test_ocv_is_a_characteristic_limit(provider):
    doc = _set(_empty(provider), "OCV", 5)            # 3 + 5 = 8
    assert judge(doc, limits=(CH("OCV", 8),), template_provider=provider).sound
    assert not judge(doc, limits=(CH("OCV", 7),),
                     template_provider=provider).sound


def test_a_limit_on_a_characteristic_the_template_removed_is_refused(provider):
    """Review Focus 1: Base6E has no SPD; never a silent 0 that passes."""
    doc = _empty(provider, Template.BASE)
    with pytest.raises(LimitError, match="SPD.*builtIn.Base6E.hdt"):
        judge(doc, limits=(CH("SPD", 6),), template_provider=provider)


def test_the_cap_binds_the_character_in_hero_identity(provider):
    """Ravel's DEX is 10 out of costume and 19 in it (pinned by
    test_activation.test_ravel_is_two_different_characters). A power level
    caps the character at full strength."""
    ravel = _authored("Ravel")
    (p,) = [p for p in judge(ravel, limits=(CH("DEX", 18),),
                             template_provider=provider).problems
            if p.kind is Problem.Kind.OVER_LIMIT]
    assert p.detail == "DEX 19; the limit is 18"
    assert not [p for p in judge(ravel, limits=(CH("DEX", 19),),
                                 template_provider=provider).problems
                if p.kind is Problem.Kind.OVER_LIMIT]


# -- Defences ----------------------------------------------------------------

def D(kind, n):
    return Limit(kind, n, None, None)


def _armoured(provider, pd_levels, ed_levels):
    """An invented build with Resistant Protection split pd/ed. `Purchase`
    states one `levels`, so the split is written on the row the way the
    build doc carries it (``pd_levels``/``ed_levels``)."""
    from kirby_cost.builder import Replace
    doc = _with(_empty(provider), provider,
                _power("FORCEFIELD", pd_levels + ed_levels))
    row = doc["powers"][0]
    return apply(doc, [Replace(row["id"], {**row, "pd_levels": pd_levels,
                                          "ed_levels": ed_levels})])


def _over(doc, provider, *limits):
    return [p for p in judge(doc, limits=limits,
                             template_provider=provider).problems
            if p.kind is Problem.Kind.OVER_LIMIT]


def test_resistant_defence_over_its_cap_is_over_limit(provider):
    doc = _armoured(provider, 10, 10)
    (p,) = _over(doc, provider, D(Limit.Kind.RESISTANT_PD, 9))
    assert p.hd_id is None
    assert p.detail == "resistant PD 10; the limit is 9"
    assert not _over(doc, provider, D(Limit.Kind.RESISTANT_PD, 10))


def test_total_defence_counts_the_resistant_part_once(provider):
    """HD's PD figure already includes Resistant Protection: Superheroic
    base PD 2, plus 5 bought, plus 10 resistant, is 17 -- not 27."""
    doc = _set(_armoured(provider, 10, 10), "PD", 5)
    (p,) = _over(doc, provider, D(Limit.Kind.PD, 16))
    assert p.detail == "PD 17; the limit is 16"
    assert not _over(doc, provider, D(Limit.Kind.PD, 17))


def test_bokors_defences(provider):
    """Bokor (Heroic6E): PD and ED at base 2, nothing bought, and Resistant
    Protection 10 PD / 10 ED, all read off his build doc. So 12 PD / 12 ED,
    10 of each resistant."""
    bokor = _authored("Bokor")
    for kind, value in ((Limit.Kind.PD, 12), (Limit.Kind.ED, 12),
                        (Limit.Kind.RESISTANT_PD, 10),
                        (Limit.Kind.RESISTANT_ED, 10)):
        assert not _over(bokor, provider, D(kind, value)), kind
        assert len(_over(bokor, provider, D(kind, value - 1))) == 1, kind


def test_the_larger_of_hds_two_figures_is_capped(provider):
    """Ravel's large Resistant Protection does not affect his primary
    figure: HD shows 7/27 PD and 0/20 rPD. A cap binds his best defence."""
    ravel = _authored("Ravel")
    (p,) = _over(ravel, provider, D(Limit.Kind.RESISTANT_PD, 19))
    assert p.detail == "resistant PD 20; the limit is 19"
    (p,) = _over(ravel, provider, D(Limit.Kind.PD, 26))
    assert p.detail == "PD 27; the limit is 26"


# -- Damage Classes (6E2 98-100) -------------------------------------------

def DC(n, counts=BOOK_DAMAGE_ADVANTAGES):
    return Limit(Limit.Kind.DAMAGE_CLASSES, n, None, counts)


def _equipment(xmlid, levels):
    return Purchase(Kind.EQUIPMENT, xmlid, levels, "", None, (), ())


def test_a_blast_is_a_damage_class_a_die(provider):
    doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 8))
    assert not _over(doc, provider, DC(8))
    (p,) = _over(doc, provider, DC(7))
    assert p.hd_id == doc["powers"][0]["id"]
    assert p.detail == "Damage Classes 8; the limit is 7"


def test_a_killing_die_is_three(provider):
    doc = _with(_empty(provider), provider, _power("RKA", 2))
    (p,) = _over(doc, provider, DC(5))
    assert p.detail == "Damage Classes 6; the limit is 5"


def test_a_mental_blast_die_is_two(provider):
    """6E2 99's table: Mental Blast is 10 Active Points a die, so 2d6 is
    4 DCs."""
    doc = _with(_empty(provider), provider, _power("EGOATTACK", 2))
    (p,) = _over(doc, provider, DC(3))
    assert p.detail == "Damage Classes 4; the limit is 3"


def test_an_advantage_that_changes_the_damage_counts(provider):
    """6E2 99: Armor Piercing affects how the victim takes damage, so a
    Blast 8d6 Armor Piercing (50 Active Points) is 10 DCs."""
    doc = _with(_empty(provider), provider,
                _power("ENERGYBLAST", 8, Pick("ARMORPIERCING", 1, None)))
    (p,) = _over(doc, provider, DC(9))
    assert p.detail == "Damage Classes 10; the limit is 9"
    assert not _over(doc, provider, DC(10))


def test_an_advantage_that_does_not_change_the_damage_does_not(provider):
    """6E2 99: Reduced Endurance does not count. Blast 8d6, ½ END is 50
    Active Points and still 8 DCs."""
    doc = _with(_empty(provider), provider,
                _power("ENERGYBLAST", 8, Pick("REDUCEDEND", 0, "HALFEND")))
    assert build_from_json(doc).powers[0].active_cost == 50
    assert not _over(doc, provider, DC(8))


def test_the_gm_decides_which_advantages_count(provider):
    """6E2 100: 'the final decision is up to the GM'. A GM who counts no
    Advantages sees the Armor Piercing Blast as its 8 dice."""
    doc = _with(_empty(provider), provider,
                _power("ENERGYBLAST", 8, Pick("ARMORPIERCING", 1, None)))
    assert not _over(doc, provider, DC(8, counts=()))


def test_a_weapon_bought_as_equipment_is_an_attack(provider):
    """Review Focus 3."""
    rifle = _with(_empty(provider), provider, _equipment("RKA", 3))
    assert not _over(rifle, provider, DC(10))                # 9 DC
    big = _with(_empty(provider), provider, _equipment("RKA", 4))
    (p,) = _over(big, provider, DC(10))
    assert p.hd_id == big["equipment"][0]["id"]
    assert p.detail == "Damage Classes 12; the limit is 10"


def test_a_power_that_does_no_damage_has_no_damage_classes(provider):
    doc = _with(_empty(provider), provider, _power("FLIGHT", 20))
    flight = doc["powers"][0]["id"]
    assert flight not in _by_id(_over(doc, provider, DC(0)))


# -- Final review fixes --------------------------------------------------------

def test_a_template_that_does_not_resolve_cannot_pass_a_characteristic_cap(provider):
    """A Base6E build whose doc names no template ("" is a statement) or one
    the provider cannot resolve is checked against what the build HAS, never
    against the fallback template's list: SPD on it is refused, not 0."""
    base = _empty(provider, Template.BASE)
    for name in ("", "builtIn.NoSuch6E.hdt"):
        doc = {**base, "template": name}
        with pytest.raises(LimitError, match="SPD"):
            judge(doc, limits=(CH("SPD", 1),), template_provider=provider)


def _str_power_on_base(provider):
    """STR 50 bought in the characteristics, plus a +0 STR power whose
    Penetrating applies to the base STR (add_modifiers_to_base): the engine
    prices the Advantage on all 60 STR."""
    doc = _set(_empty(provider), "STR", 50)
    doc = _with(doc, provider, _power("STR", 0, Pick("PENETRATING", 1, None)))
    from kirby_cost.builder import Replace
    row = doc["powers"][0]
    return apply(doc, [Replace(row["id"], {**row, "add_modifiers_to_base": True})])


def _every_advantage(obj):
    mods = list(obj.assigned_modifiers)
    parent = getattr(obj, "parent", None)
    if parent is not None:
        mods += list(parent.assigned_modifiers)
    return tuple(DamageAdvantage(m.xmlid, None, None) for m in mods)


def test_a_characteristic_bought_as_a_power_is_priced_as_the_engine_prices_it(provider):
    doc = _str_power_on_base(provider)
    (power,) = build_from_json(doc).powers
    assert power.active_cost > 0
    (p,) = [p for p in _over(doc, provider, DC(0, counts=(
        DamageAdvantage("PENETRATING", None, None),))) if p.hd_id == str(power.id)]
    assert p.detail == f"Damage Classes {power.active_cost / 5:g}; the limit is 0"


@pytest.mark.parametrize("name", ["Ravel", "Bokor", "PowerLad", "invented STR"])
def test_counting_every_advantage_gives_back_the_active_points(name, provider):
    """Parity: with every Advantage counted, DCs x 5 is the engine's own
    Active Points, for every damaging purchase -- so no purchase's own
    pricing is bypassed."""
    from kirby_cost.builder.limits import _measured_purchases, _parts
    from kirby_cost.engine.damage import damage_classes_of
    doc = (_str_power_on_base(provider) if name == "invented STR"
           else _authored(name))
    hero = build_from_json(doc)
    checked = 0
    for obj in _measured_purchases(hero):
        for part in _parts(obj):
            if part.does_damage:
                assert damage_classes_of(part, _every_advantage(part)) * 5 \
                    == part.active_cost, (part.xmlid, part.id)
                checked += 1
    assert checked


def test_a_purchase_priced_by_its_own_rule_and_not_the_core_is_refused():
    """A class with its own active-cost pricing that has not moved onto the
    shared core would be priced wrong for DCs; it raises instead."""
    from kirby_cost.engine.damage import damage_classes_of

    class OwnPricing:
        does_damage = True
        xmlid = "ODD"

        def _compute_active_cost(self, exclude_xmlid):
            return 99.0

    with pytest.raises(TypeError, match="ODD"):
        damage_classes_of(OwnPricing(), BOOK_DAMAGE_ADVANTAGES)


# -- Martial Arts and STR count toward a DC ceiling (Peter, 2026-11-26) -------
#
# A maneuver's Damage Classes are the ones HD itself totals and prints in its
# effect: the maneuver's own DCs, plus Extra DCs, plus STR/5 when it adds STR
# (6E2 99-101). A character's STR is an attack of STR/5 DCs (6E1 137).

RAVEL_JOINT_LOCK = "1648502990626"          # DC 2: "1d6 NND"
RAVEL_GRAPPLING_BLOCK = "1648370660426"     # adds STR, but a Block does no damage


def _maneuver_row(hd_id, display, dc, effect, add_str, use_weapon=False):
    """A maneuver row as a build doc carries one, the way Ravel's are
    written; only the damage fields vary."""
    return {"id": hd_id, "xmlid": "MANEUVER", "base_cost": 4.0,
            "alias": display, "maneuver": True, "category": "Hand To Hand",
            "display": display, "ocv": "+0", "dcv": "+2", "dc": dc,
            "phase": "1/2", "effect": effect, "add_str": add_str,
            "maneuver_active_cost": 20, "damage_type": 0, "max_str": 0,
            "str_multiplier": 1, "use_weapon": use_weapon,
            "weapon_effect": "Weapon [WEAPONDC] Strike"}


def _with_martial(doc, *rows):
    return {**doc, "martial_arts": [*doc["martial_arts"], *rows]}


def _by_id(problems):
    return {p.hd_id: p.detail for p in problems}


def test_a_maneuver_that_does_damage_is_measured(provider):
    """Ravel's Joint Lock/Throw is 2 DCs (HD prints 1d6 NND); his
    Grappling Block adds STR to the grab but does no damage, so is not an
    attack at all."""
    ravel = _authored("Ravel")
    over = _by_id(_over(ravel, provider, DC(1)))
    assert over[RAVEL_JOINT_LOCK] == "Damage Classes 2; the limit is 1"
    assert RAVEL_GRAPPLING_BLOCK not in over
    assert RAVEL_JOINT_LOCK not in _by_id(_over(ravel, provider, DC(2)))


def test_a_maneuver_that_adds_str_counts_the_str(provider):
    """6E2 101: a Martial Strike adds its +2 DC to the character's STR.
    Ravel's STR 10 is 2 DCs, so the Strike is 4."""
    doc = _with_martial(_authored("Ravel"), _maneuver_row(
        "9000000000001", "Martial Strike", 2, "[NORMALDC] Strike", True))
    over = _by_id(_over(doc, provider, DC(3)))
    assert over["9000000000001"] == "Damage Classes 4; the limit is 3"
    assert "9000000000001" not in _by_id(_over(doc, provider, DC(4)))


def test_extra_damage_classes_count_on_every_hand_to_hand_maneuver(provider):
    """Extra DCs bought with the art add to each Hand-to-Hand maneuver."""
    doc = _with_martial(
        _authored("Ravel"),
        _maneuver_row("9000000000001", "Martial Strike", 2,
                      "[NORMALDC] Strike", True),
        {"id": "9000000000002", "xmlid": "EXTRADC", "levels": 2,
         "alias": "+2 HTH Damage Class(es)"})
    over = _by_id(_over(doc, provider, DC(3)))
    assert over["9000000000001"] == "Damage Classes 6; the limit is 3"
    assert over[RAVEL_JOINT_LOCK] == "Damage Classes 4; the limit is 3"


def test_str_bought_as_a_characteristic_is_an_attack(provider):
    """6E1 137: 1d6 of damage per 5 STR. STR 50 is a 10 DC punch."""
    doc = _set(_empty(provider), "STR", 40)
    (p,) = [p for p in _over(doc, provider, DC(9)) if p.hd_id is None]
    assert p.detail == "STR Damage Classes 10; the limit is 9"
    assert not [p for p in _over(doc, provider, DC(10)) if p.hd_id is None]


def test_an_authored_characters_str_is_measured(provider):
    """PowerLad's STR 40 is 8 DCs."""
    powerlad = _authored("PowerLad")
    assert _by_id(_over(powerlad, provider, DC(7)))[None] \
        == "STR Damage Classes 8; the limit is 7"
