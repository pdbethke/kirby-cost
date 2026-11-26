"""`judge` holds a build to its power level.

Character-workshop spec §5.2: a limit breach is reported exactly like an
illegal modifier -- ``Problem.Kind.OVER_LIMIT``, the purchase's HD ``ID`` (or
None for a whole-character measure), and what was measured against what.
Limits are maxima: a build AT a limit is inside it.
"""
from __future__ import annotations

import pytest

from kirby_cost.builder import (
    Kind, Limit, LimitError, Problem, Purchase, Template, apply, buy, judge,
    new_build,
)
from kirby_cost.io.build_json import to_build_json
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
    return Limit(Limit.Kind.ACTIVE_POINTS, n, None)


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


def test_a_kind_nothing_yet_measures_is_refused_not_skipped(provider):
    """Temporary until every kind is measured: an unmeasured kind must
    never pass a build by being ignored."""
    doc = _empty(provider)
    with pytest.raises(LimitError, match="RESISTANT_ED"):
        judge(doc, limits=(Limit(Limit.Kind.RESISTANT_ED, 10, None),),
              template_provider=provider)


# -- Characteristic maxima (OCV, DCV, SPD, ...) -------------------------------

def CH(xmlid, n):
    return Limit(Limit.Kind.CHARACTERISTIC_MAX, n, xmlid)


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
