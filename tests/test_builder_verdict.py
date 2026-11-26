"""The builder's fourth layer: the engine's verdict on a build.

An AI's build is never trusted (Peter, 2026-11-24: the AI builds NPCs,
bases, equipment). `judge` costs the build and reports every problem in the
engine's own words: a modifier HD would refuse on its power (HD's
verifyModifiers(), `validation.verify`), and points spent beyond what the
build has (HD's own `available_points`). An empty list of problems is a
sound build; the caller decides what to do with one that is not.
"""
from __future__ import annotations

import pytest

from kirby_cost.builder import (
    Kind, Pick, Problem, Purchase, Template, apply, buy, judge, new_build,
)
from kirby_cost.template.hdt_provider import HDTTemplateProvider


@pytest.fixture(scope="module")
def provider():
    return HDTTemplateProvider()


def _empty(provider, base_points=400):
    return new_build(Template.SUPERHEROIC, template_provider=provider,
                     name="Test NPC", base_points=base_points, disad_points=0,
                     experience=0)


def _with(doc, provider, *purchases):
    for p in purchases:
        doc = apply(doc, [buy(doc, p, template=provider)])
    return doc


def _power(xmlid, levels, *mods):
    return Purchase(Kind.POWER, xmlid, levels, "", None, (), tuple(mods))


def test_a_sound_build_has_no_problems(provider):
    doc = _with(_empty(provider), provider, _power("ENERGYBLAST", 8))
    verdict = judge(doc, limits=(), template_provider=provider)
    assert verdict.problems == ()
    assert verdict.total_points == 40
    assert verdict.available_points == 360


def test_a_modifier_hd_refuses_is_a_problem_in_hds_words(provider):
    doc = _with(_empty(provider), provider,
                _power("FLIGHT", 4, Pick("AOE", 0, None)))
    (problem,) = judge(doc, limits=(), template_provider=provider).problems
    assert problem.kind is Problem.Kind.ILLEGAL_MODIFIER
    assert problem.xmlid == "AOE"
    assert "targeted on others" in problem.detail
    (flight,) = doc["powers"]
    assert problem.hd_id == flight["id"]


def test_spending_more_than_the_build_has_is_a_problem(provider):
    doc = _with(_empty(provider, base_points=20), provider,
                _power("ENERGYBLAST", 8))
    (problem,) = judge(doc, limits=(), template_provider=provider).problems
    assert problem.kind is Problem.Kind.OVER_POINTS
    assert "20" in problem.detail and "40" in problem.detail
