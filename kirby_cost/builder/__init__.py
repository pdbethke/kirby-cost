"""The builder: make and change builds through the engine.

Two-databases spec §4a. Layered so each layer is usable on its own:

1. `edits` — add, replace or remove an element of a build doc by HD ``ID``,
   refusing by name anything that does not fit (a campaign's overrides over
   a codex base; an AI's proposed changes).

Later layers (template elements by XMLID, a new build from any template, a
verdict with costs and validation findings) build on this one.
"""
from kirby_cost.builder.edits import Add, Edit, EditConflict, Remove, Replace, apply

__all__ = ["Add", "Edit", "EditConflict", "Remove", "Replace", "apply"]
