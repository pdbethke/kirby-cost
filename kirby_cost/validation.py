"""Validation -- the three questions a character builder asks before adding
a modifier, answered the way Hero Designer answers them.

    >>> from kirby_cost import check
    >>> from tests.matrix_support import template_power
    >>> blast = template_power("ENERGYBLAST")  # a builder's in-progress power
    >>> check("ZEROPHASE", blast).reason
    'Powers Can Be Changed As A Zero-Phase Action can only be applied to abilities of type vpp'

HD keeps three separate surfaces and so does this module:

* ``check``              -- Modifier.included(): may this modifier go here,
                            and if not, why (HD's own message).
* ``allowed_modifiers``  -- what the "add a modifier" list shows: every
                            template modifier, each with its verdict, so a
                            UI can grey the refused ones with their reason.
* ``exclusive_conflict`` -- the add-time rule HD keeps OUTSIDE included():
                            an EXCLUSIVE modifier may appear once per object.

Pure: no session, no database, no I/O beyond reading the template once.
Nothing here decides a rule; the rules are ``Modifier.included`` (ported
from Modifier.java:763 and proved against HD's own verdicts by
tests/test_included_matrix.py) and the template's EXCLUSIVE flag. This is
the door, not the rule.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from kirby_cost.objects.base import GenericObject
from kirby_cost.template.dataclasses import TemplateData
from kirby_cost.template.hdt_provider import HDTTemplateProvider
from kirby_cost.template.prototypes import modifier_prototype


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    reason: str = ""


@lru_cache(maxsize=1)
def _provider() -> HDTTemplateProvider:
    return HDTTemplateProvider()


def check(modifier_xmlid: str, obj: GenericObject, *, option_id: str | None = None) -> Verdict:
    """May ``modifier_xmlid`` go on ``obj``? HD's answer, HD's words."""
    mod = modifier_prototype(modifier_xmlid, option_id)
    if mod is None:
        return Verdict(False, f"unknown modifier: {modifier_xmlid!r}")
    reason = mod.included(obj) or ""
    return Verdict(reason.strip() == "", reason)


def allowed_modifiers(obj: GenericObject) -> list[tuple[TemplateData, Verdict]]:
    """Every template modifier with its verdict for ``obj``, in template order."""
    out: list[tuple[TemplateData, Verdict]] = []
    for (section, xmlid), data in _provider()._by_section.items():
        if section != "modifiers":
            continue
        out.append((data, check(xmlid, obj)))
    return out


def exclusive_conflict(modifier_xmlid: str, obj: GenericObject) -> Verdict:
    """Refuse a second instance of an EXCLUSIVE modifier on the same object."""
    xmlid = (modifier_xmlid or "").upper().strip()
    data = _provider().get_template_data(xmlid, section="modifiers")
    if data is None:
        return Verdict(False, f"unknown modifier: {modifier_xmlid!r}")
    if data.exclusive:
        for mod in getattr(obj, "assigned_modifiers", None) or []:
            if (mod.xmlid or "").upper() == xmlid:
                return Verdict(False, f"{data.display} is already on {obj.display}; it may be applied only once.")
    return Verdict(True, "")
