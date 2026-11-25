"""A build doc states its name, template and point totals: no defaults.

`_root_from_doc` used to fill a missing ``base_points`` with 400,
``disad_points`` with 75 and ``experience`` with 0 (a Superheroic
character's numbers), and `to_build_json` read them off the hero with the
same fallbacks. A doc that forgot them was silently costed as a 400-point
hero: a 200-point vehicle or a 0-XP NPC came back with the wrong budget and
nothing said so. Found 2026-11-25 building the shared build-object store,
which persists these as columns. Peter's rule: no defaults.
"""
from __future__ import annotations

import pytest

from kirby_cost.io.build_json import BuildDocError, build_from_json

REQUIRED = ("name", "template", "base_points", "disad_points", "experience")


def _doc():
    return {"name": "Nobody", "template": "builtIn.Superheroic6E.hdt",
            "base_points": 200, "disad_points": 0, "experience": 5,
            "characteristics": [], "powers": []}


def test_a_doc_that_states_them_is_costed_on_them():
    hero = build_from_json(_doc())
    assert (hero.base_points, hero.disad_points, hero.experience) == (200, 0, 5)


@pytest.mark.parametrize("field", REQUIRED)
def test_a_doc_missing_one_is_refused_by_name(field):
    doc = _doc()
    del doc[field]
    with pytest.raises(BuildDocError, match=field):
        build_from_json(doc)
