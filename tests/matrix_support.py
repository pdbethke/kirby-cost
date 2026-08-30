"""Build template prototypes the way the loader would, with no character.

The matrix asks "may modifier M go on power P" for every M and P the template
defines. HD answers with prototype objects straight from the template
(``Template.getModifiers()`` / ``getPowers()``); this builds the engine's
equivalents. Powers use the registered class when there is one and the
loader's ``_FallbackObject`` otherwise -- exactly the loader's own dispatch --
then take the template's defaults (duration, target, range, types). Modifiers
come from the registry too, so subclass ``included()`` overrides run.

HD computes the matrix with a blank character open, because 22 modifier
subclasses read the active hero; ``blank_hero_context()`` gives the engine
the same context.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from kirby_cost.io.hdc_loader import HDCLoader, _FallbackObject
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier

FIXTURE = Path(__file__).parent / "fixtures" / "included_matrix.json"


def blank_hero_context() -> None:
    """HD computes the matrix with a blank character open (22 modifier
    subclasses read the active hero); the engine gets the same context."""
    from kirby_cost.core.context import EngineContext
    from kirby_cost.io.hdc_loader import LoadedHero
    EngineContext.set_active_hero(LoadedHero())


@lru_cache(maxsize=1)
def _loader() -> HDCLoader:
    loader = HDCLoader()
    loader._ensure_registry_loaded()
    return loader


@lru_cache(maxsize=1)
def matrix() -> dict:
    return json.loads(FIXTURE.read_text())


def cells() -> list[dict]:
    return matrix()["cells"]


def cell_key(modifier: str, power: str) -> str:
    return f"{modifier}-on-{power}"


def template_power(xmlid: str) -> GenericObject:
    loader = _loader()
    cls = loader._get_power_cls(xmlid) or _FallbackObject
    obj = cls()
    obj.xmlid = xmlid
    loader._apply_template_defaults(obj, xmlid, None)
    return obj


def template_modifier(xmlid: str) -> Modifier:
    loader = _loader()
    cls = GenericObject._registry.get(xmlid)
    mod = cls() if (cls is not None and issubclass(cls, Modifier)) else Modifier()
    mod.xmlid = xmlid
    loader._apply_template_to_modifier(mod, xmlid, None)
    return mod
