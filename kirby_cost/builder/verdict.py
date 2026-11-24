"""The engine's verdict on a build: what it costs and what is wrong with it.

The builder's fourth layer (two-databases spec §4a). An AI's build is never
trusted (Peter, 2026-11-24: the AI builds NPCs, bases, equipment), and a
campaign's blended build is checked the same way. `judge` loads and costs
the build, then reports every problem in the engine's own words:

* ``ILLEGAL_MODIFIER`` — a modifier HD would refuse on its purchase: HD's
  ``verifyModifiers()`` (`kirby_cost.validation.verify`), which for a
  framework also checks each common modifier against each slot;
* ``OVER_POINTS`` — points spent beyond what the build has, by HD's own
  oracle-verified `LoadedHero.available_points`.

An empty ``problems`` is a sound build. What to do with one that is not
(refuse it, ask the AI again, show the GM) is the caller's decision.

KNOWN LIMIT: `validation` checks modifiers against the configured template
(``KIRBY_COST_HDT``), not the build's declared one; a modifier rule that a
specialised template changes is judged by Main6E's.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from kirby_cost.io.formats import load_build


@dataclass(frozen=True)
class Problem:
    """One thing wrong with a build."""

    class Kind(Enum):
        ILLEGAL_MODIFIER = "illegal_modifier"
        OVER_POINTS = "over_points"

    kind: "Problem.Kind"
    #: The purchase it is about (its HD ``ID``), or None for the whole build.
    hd_id: str | None
    #: The modifier at fault, or None.
    xmlid: str | None
    detail: str


@dataclass(frozen=True)
class BuildVerdict:
    total_points: float
    available_points: float
    problems: tuple[Problem, ...]

    @property
    def sound(self) -> bool:
        return not self.problems


def _purchases(hero):
    for section in ("characteristics", "skills", "perks", "talents",
                    "martial_arts", "powers", "equipment", "complications"):
        yield from getattr(hero, section, None) or []


def judge(doc: dict) -> BuildVerdict:
    """Cost ``doc`` (a JSON build doc) and report every problem with it."""
    from kirby_cost.validation import verify

    hero = load_build(doc, format="json")
    problems: list[Problem] = []
    for obj in _purchases(hero):
        for finding in verify(obj):
            problems.append(Problem(
                Problem.Kind.ILLEGAL_MODIFIER,
                str(finding.slot_id or obj.id), finding.modifier_xmlid,
                finding.verdict.reason))
    total, available = hero.total_points, hero.available_points
    if available < 0:
        budget = total + available
        problems.append(Problem(
            Problem.Kind.OVER_POINTS, None, None,
            f"spends {total:g} points of {budget:g}: {-available:g} over"))
    return BuildVerdict(total_points=total, available_points=available,
                        problems=tuple(problems))


__all__ = ["BuildVerdict", "Problem", "judge"]
