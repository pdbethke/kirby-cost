"""The builder: make and change builds through the engine.

Two-databases spec §4a. Layered so each layer is usable on its own:

All four work on the CURATED build doc (`kirby_cost.io.build_json`), the
shape a relational store keeps, so a stored row and an edit's payload are
the same thing (Peter, 2026-11-25).

1. `edits` — add, replace or remove a purchase in a build doc by HD ``ID``,
   refusing by name anything that does not fit (a campaign's overrides over
   a codex base; an AI's proposed changes).

2. `purchases` — a purchase named by XMLID (levels, name, option, adders,
   modifiers) made into an element, every name checked against the
   template; costs come from the template when the build is loaded.

3. `new` — a new, empty build on any HD template (an NPC, a base, a
   vehicle), holding exactly the characteristics HD gives it.

4. `verdict` — `judge(doc)`: the build costed, and every problem in the
   engine's own words (a modifier HD refuses; points over budget).

5. `limits` — `PowerLevel` and `Limit`: a campaign's power level, the
   ceilings `judge` holds a build to (character-workshop spec §5.2).
"""
from kirby_cost.builder.edits import (
    Add, Edit, EditConflict, Remove, Replace, apply, ids, purchases,
)
from kirby_cost.io.build_json import Section
from kirby_cost.builder.new import Template, new_build
from kirby_cost.builder.verdict import BuildVerdict, Problem, judge
from kirby_cost.builder.limits import Limit, LimitError, PowerLevel
from kirby_cost.builder.purchases import (
    Kind, NotInTemplate, Pick, Purchase, buy, element,
)

__all__ = [
    "Add", "BuildVerdict", "Edit", "EditConflict", "Kind", "Limit", "LimitError", "PowerLevel", "Problem", "judge", "NotInTemplate", "Pick",
    "Purchase", "Remove", "Replace", "Section", "Template", "apply", "buy",
    "element", "ids", "new_build", "purchases",
]
