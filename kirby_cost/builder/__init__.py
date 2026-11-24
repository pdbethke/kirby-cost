"""The builder: make and change builds through the engine.

Two-databases spec §4a. Layered so each layer is usable on its own:

1. `edits` — add, replace or remove an element of a build doc by HD ``ID``,
   refusing by name anything that does not fit (a campaign's overrides over
   a codex base; an AI's proposed changes).

2. `purchases` — a purchase named by XMLID (levels, name, option, adders,
   modifiers) made into an element, every name checked against the
   template; costs come from the template when the build is loaded.

Later layers (a new build from any template, a verdict with costs and
validation findings) build on these.
"""
from kirby_cost.builder.edits import Add, Edit, EditConflict, Remove, Replace, apply
from kirby_cost.builder.purchases import (
    Kind, NotInTemplate, Pick, Purchase, buy, element,
)

__all__ = [
    "Add", "Edit", "EditConflict", "Kind", "NotInTemplate", "Pick",
    "Purchase", "Remove", "Replace", "apply", "buy", "element",
]
