"""Cost service over the build doc: build_from_json then report what the build
engine's class behavior computes — total, per-object subcosts, XP/points budget."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from kirby_cost.io.build_json import build_from_json
from kirby_cost.io.hdc_loader import LoadedHero

# Order MUST match _SECTION_TAG in build_json.py (characteristics, powers, skills,
# perks, talents, martial_arts) so that the O{n} ids assigned here are the same ids
# that to_build_json emits — allowing per_object keys to join back to build-doc object
# ids. Disadvantages bear no cost and are excluded; they come last in _SECTION_TAG's
# numbering, so excluding them does not offset the earlier ids. martial_arts is placed
# before disadvantages in _SECTION_TAG and therefore appears here after talents.
_BUILD_LISTS = ("characteristics", "powers", "skills", "perks", "talents", "martial_arts")

@dataclass
class CostResult:
    total_cost: int                       # canonical rounded total
    total_cost_exact: float               # UNROUNDED — for live tweaking
    base_points: int
    disad_points: int
    experience: int
    available_points: float
    points_spent: float
    per_object: dict[str, dict[str, float]] = field(default_factory=dict)

from kirby_cost.io.build_json import _doc_id  # noqa: E402


def extract_costs(hero: LoadedHero) -> CostResult:
    """Read the loaded build's live cost properties into a CostResult.

    available_points: LoadedHero has no such property — it lives on
    kirby_cost.model.hero.Hero (the DB-backed model). The fallback
    computes it inline as base_points + disad_points + experience - spent,
    using disad_points (the campaign allowance) rather than Hero.available_points'
    disads_used, because LoadedHero does not resolve disadvantage real costs.
    """
    per_object: dict[str, dict[str, float]] = {}
    exact = 0.0
    idx = 0
    for attr in _BUILD_LISTS:
        for o in getattr(hero, attr, []):
            idx += 1
            rc = float(getattr(o, "real_cost", 0) or 0)
            exact += rc
            # Keyed by the SAME rule the document uses (build_json._doc_id):
            # HD's own ID where the object has one, synthetic O<n> only where
            # it does not. These keys exist to join back to the doc, so a
            # second numbering scheme here means they join to nothing — which
            # is what happened the moment the doc started stating real ids.
            per_object[_doc_id(o, idx)] = {
                "base_cost": float(getattr(o, "base_cost", 0) or 0),
                "active_cost": float(getattr(o, "active_cost", 0) or 0),
                "real_cost": rc,
            }
    base = int(getattr(hero, "base_points", 0) or 0)
    disad = int(getattr(hero, "disad_points", 0) or 0)
    xp = int(getattr(hero, "experience", 0) or 0)
    # LoadedHero has no available_points property; Hero (model) does but is
    # DB-backed. Compute inline using disad_points (the campaign allowance) rather
    # than Hero.available_points' disads_used, because LoadedHero does not resolve
    # disadvantage real costs; for the build-doc path the allowance is the budget
    # contributor.
    available = float(base + disad + xp - exact)
    return CostResult(
        total_cost=int(round(exact)), total_cost_exact=exact,
        base_points=base, disad_points=disad, experience=xp,
        available_points=available, points_spent=exact, per_object=per_object,
    )

def cost_build(doc: dict[str, Any]) -> CostResult:
    return extract_costs(build_from_json(doc))
