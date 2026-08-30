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


def cell_key(modifier: str, power: str, node: str = "") -> str:
    return f"{modifier}-on-{power}" if not node else f"{modifier}-on-{power}[{node}]"


def template_power(xmlid: str, node: str = "") -> GenericObject:
    # HD's power enumeration carries its category nodes, which are
    # com.hero.objects.List instances (Template.java:1627) and so keep
    # GenericObject's default XMLID of GENERIC_OBJECT. Modifier.included()
    # branches on `power instanceof List`, so the prototype has to be a List
    # or every typed modifier answers the wrong question.
    if xmlid == "GENERIC_OBJECT":
        from kirby_cost.objects.list import List as HeroList
        obj = HeroList()
        obj.xmlid = xmlid
        if node:
            obj._display = node
        return obj
    loader = _loader()
    # RUNNING, LEAPING and SWIMMING are CHARACTERISTICS in Main6E, not powers,
    # so the loader's power dispatch does not find them and they fell to
    # _FallbackObject with TARGET "N/A". HD's object is the Characteristic,
    # whose init sets TARGET="SELFONLY" and DURATION="PERSISTENT"
    # (Characteristic.java:1826-1844), and three self-only rules branch on it.
    # The engine has the classes -- they are just in the general registry
    # rather than the power one.
    cls = loader._get_power_cls(xmlid) or GenericObject._registry.get(xmlid) or _FallbackObject
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


STATEFUL_FIXTURE = Path(__file__).parent / "fixtures" / "included_stateful.json"


@lru_cache(maxsize=1)
def stateful_cells() -> list[dict]:
    return json.loads(STATEFUL_FIXTURE.read_text())["cells"]


def stateful_key(cell: dict) -> str:
    key = f"{cell['tier']}:{cell['object_id']}:{cell['modifier']}"
    return f"{key}:{cell['option_id']}" if cell.get("option_id") else key


def hdc_id(obj) -> str:
    """The HDC ``ID`` attribute, as a string. Delegates to the library's own
    ``GenericObject.hdc_id()`` (base.py) -- that is the one accessor for
    ``_id``, and ``kirby_cost.validation.verify`` uses the same one."""
    return obj.hdc_id()


def allows_other_modifiers(obj) -> bool:
    """``GenericObject.allows_other_modifiers`` is a bool attribute on the
    base class but a METHOD override on a handful of subclasses (martial
    arts elements, ``Disadvantage``) -- call it if callable, else read it."""
    val = obj.allows_other_modifiers
    return val() if callable(val) else val


@lru_cache(maxsize=1)
def _built_sink_hero():
    """The validation sink, loaded through the REAL loader -- built once and
    cached, since ``HDCLoader.load_file`` is the expensive part."""
    import tempfile
    from tests.validation_sink import write
    path = Path(tempfile.gettempdir()) / "kirby-cost-ValidationSink.hdc"
    write(path)
    return _loader().load_file(str(path))


def sink_hero():
    """The validation sink, installed as the active hero (six overrides
    read it, exactly as HD's do). Re-arms ``EngineContext`` on EVERY call,
    not only the first: ``_built_sink_hero()`` is cached, but the active
    hero is process-wide mutable state -- another test (``blank_hero_context()``
    for the applicability matrix's blank-character survey, most often) can
    leave it pointing elsewhere between calls, and a caller relying on a
    cache hit to also mean "the hero is still active" got the blank
    context's answers instead of the sink's."""
    from kirby_cost.core.context import EngineContext
    hero = _built_sink_hero()
    EngineContext.set_active_hero(hero)
    return hero


def object_index(hero) -> dict[str, GenericObject]:
    """HDC ID attribute -> loaded object, every section, recursing into lists
    (``List.objects``) and Compound Power constituents (``.powers``)."""
    out: dict[str, GenericObject] = {}

    def walk(objs):
        for o in objs:
            out[hdc_id(o)] = o
            walk(getattr(o, "objects", None) or [])   # List slots
            walk(getattr(o, "powers", None) or [])    # CompoundPower children

    for section in ("characteristics", "skills", "perks", "talents", "powers", "equipment"):
        walk(getattr(hero, section, []) or [])
    return out


def template_modifier(xmlid: str) -> Modifier:
    # Built by kirby_cost.template.prototypes.modifier_prototype -- the SAME
    # prototype kirby_cost.validation.check() hands out, so this matrix test
    # proves the object the validation door actually uses. See that module
    # for how LEVELSTART and the template are applied.
    from kirby_cost.template.prototypes import modifier_prototype
    mod = modifier_prototype(xmlid)
    if mod is None:
        raise KeyError(f"no template modifier: {xmlid!r}")
    return mod
