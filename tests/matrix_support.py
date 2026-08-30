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
    # HD's power enumeration carries its category nodes, which are
    # com.hero.objects.List instances (Template.java:1627) and so keep
    # GenericObject's default XMLID of GENERIC_OBJECT. Modifier.included()
    # branches on `power instanceof List`, so the prototype has to be a List
    # or every typed modifier answers the wrong question.
    if xmlid == "GENERIC_OBJECT":
        from kirby_cost.objects.list import List as HeroList
        obj = HeroList()
        obj.xmlid = xmlid
        return obj
    loader = _loader()
    cls = loader._get_power_cls(xmlid) or _FallbackObject
    obj = cls()
    obj.xmlid = xmlid
    loader._apply_template_defaults(obj, xmlid, None)
    # HD builds a prototype FROM the template entry, so the template's
    # DURATION is the last word. The engine's loader applies it only when the
    # class constructor left `_duration` empty (hdc_loader/base.py's
    # "only if it has no duration" guard), so a class that hardcodes one --
    # ForceWall and Telepathy both say CONSTANT where Main6E says INSTANT --
    # keeps the wrong value and every duration rule answers the wrong
    # question. Corrected here, on the prototype only; the loader's own
    # precedence is a separate defect (see the Task 6 report).
    tmpl = loader._get_template_data(xmlid, obj)
    if tmpl is not None and getattr(tmpl, "duration", None):
        obj._duration = tmpl.duration
    # HD's prototype also carries the template's BASECOST and LEVELSTART, so it
    # has a cost, and getRangeValue() derives a ranged power's reach from that
    # cost. The engine's loader leaves both at zero for an object no .hdc ever
    # stated, so every ranged prototype read as reaching 0m.
    if tmpl is not None:
        if not obj.base_cost and tmpl.base_cost:
            obj.base_cost = tmpl.base_cost
        if not obj.levels and getattr(tmpl, "level_start", 0):
            obj.levels = tmpl.level_start
        # CONTINUINGEFFECT, likewise: Main6E states it on Entangle, Barrier,
        # Summon and 20 others, the loader never applies it, and two duration
        # rules branch on it (CostsENDToMaintain.java:63,68). Java's
        # continuingEffect() is a plain FIELD read (GenericObject.java
        # :3003-3005); the engine's property ALSO infers it from the duration
        # modifiers, which is a separate divergence and is left alone -- this
        # only supplies the field HD's prototype starts with.
        if getattr(tmpl, "continuing_effect", False):
            obj.continuing_effect = True
    return obj


def template_modifier(xmlid: str) -> Modifier:
    loader = _loader()
    cls = GenericObject._registry.get(xmlid)
    mod = cls() if (cls is not None and issubclass(cls, Modifier)) else Modifier()
    mod.xmlid = xmlid
    loader._apply_template_to_modifier(mod, xmlid, None)
    # HD's modifier prototype carries the template's LEVELSTART, the same way
    # its power prototype does (see template_power). It is what getDisplay()
    # substitutes into a `[LVL]` placeholder: Main6E declares Expanded Effect
    # as `DISPLAY="Expanded Effect (x[LVL] ...)" LEVELSTART="2"` and HD prints
    # "x2". The LOADER is deliberately left alone -- an HDC modifier element
    # always states its own LEVELS, so only the prototype has none.
    tmpl = loader._get_template_data(xmlid)
    if tmpl is not None and not mod.levels and getattr(tmpl, "level_start", 0):
        mod.levels = tmpl.level_start
    return mod
