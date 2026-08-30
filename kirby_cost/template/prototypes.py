"""Build the modifier prototype the way HD's own Template.getModifiers()
would, and the way ``tests/test_included_matrix.py`` proved against the
Java oracle.

There is exactly one place that constructs this prototype: this module.
``tests/matrix_support.template_modifier`` and ``kirby_cost.validation.check``
both call ``modifier_prototype`` rather than building their own, so the
matrix test proves the same object the validation door hands out.
"""
from __future__ import annotations

from functools import lru_cache

from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.template.hdt_provider import HDTTemplateProvider


@lru_cache(maxsize=1)
def _loader() -> HDCLoader:
    loader = HDCLoader()
    loader._ensure_registry_loaded()
    return loader


@lru_cache(maxsize=1)
def _provider() -> HDTTemplateProvider:
    return HDTTemplateProvider()


def modifier_prototype(xmlid: str, option_id: str | None = None) -> Modifier | None:
    """The prototype modifier HD's own template entry describes, or ``None``
    when *xmlid* is not a modifier the template knows.

    Built from the registry class (so subclass ``included()`` overrides
    run), with the template applied and, like HD's own prototype, the
    template's LEVELSTART carried onto ``levels`` -- it is what
    ``getDisplay()`` substitutes into a ``[LVL]`` placeholder. Main6E
    declares Expanded Effect as ``DISPLAY="Expanded Effect (x[LVL] ...)"
    LEVELSTART="2"`` and HD prints "x2". An HDC modifier element always
    states its own LEVELS, so this only supplies what a bare prototype
    starts with.
    """
    xmlid = (xmlid or "").upper().strip()
    loader = _loader()
    tmpl = _provider().get_template_data(xmlid, section="modifiers")
    if tmpl is None:
        return None
    cls = GenericObject._registry.get(xmlid)
    mod = cls() if (cls is not None and issubclass(cls, Modifier)) else Modifier()
    mod.xmlid = xmlid
    if option_id:
        mod.option_id = option_id
    loader._apply_template_to_modifier(mod, xmlid, option_id)
    if not mod.levels and getattr(tmpl, "level_start", 0):
        mod.levels = tmpl.level_start
    return mod
