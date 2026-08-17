"""Build + cost ONE power from a structured spec via the engine's own loader
helpers. Cost ALWAYS comes from the engine (never hand-rolled). Used by the
a VPP reconfigure flow, to validate a proposed power against the pool.

The construction path mirrors HDCLoader exactly (registry lookup -> instantiate
-> set xmlid/levels -> apply template defaults -> per-modifier build) so the
reported active/real cost is byte-identical to the canonical loader's.
"""
from __future__ import annotations

from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.io.hdc_loader import HDCLoader


def _make_modifier(loader: HDCLoader, mx: str, m: dict) -> Modifier:
    """Build one Modifier from a spec node, mirroring HDCLoader._build_modifier.

    The XML loader path does: Modifier.get_instance(elem) (or a plain Modifier),
    sets option_id from OPTIONID, then _apply_template_to_modifier. Specs carry
    no XML element, so we set xmlid/base_cost directly and apply the template.
    ``base_cost`` is the advantage/limitation value (e.g. +1.0 for a +1 advantage).
    """
    mod = Modifier()
    mod.xmlid = mx
    option_id = (m.get("option_id") or None)
    if option_id:
        mod.option_id = option_id
    # Apply template defaults (costs, options) before overlaying the spec's value,
    # matching the loader's ordering (_apply_template_to_modifier sets base_cost
    # from the template; the explicit spec value is the authoritative override).
    loader._apply_template_to_modifier(mod, mx, option_id)
    base_cost = m.get("base_cost")
    if base_cost is not None:
        mod.base_cost = float(base_cost)
    return mod


def build_power_from_spec(spec: dict, *, loader: HDCLoader | None = None):
    """Construct the engine power for ``spec`` and return
    (power, active_cost:int, real_cost:int). Raises ValueError on unknown xmlid.

    The power is built standalone (no hero/framework context), which is correct
    for a VPP's on-the-fly powers.
    """
    loader = loader or HDCLoader()
    loader._ensure_registry_loaded()
    xmlid = (spec.get("xmlid") or "").upper()
    cls = GenericObject._registry.get(xmlid)
    if cls is None:
        raise ValueError(f"unknown power xmlid: {xmlid}")
    obj = cls()
    obj.xmlid = xmlid
    obj.levels = float(spec.get("levels") or 0)
    loader._apply_template_defaults(obj, xmlid, spec.get("option_id") or None)
    for m in (spec.get("modifiers") or []):
        mx = (m.get("xmlid") or "").upper()
        if not mx:
            continue
        mod = _make_modifier(loader, mx, m)
        obj._assigned_modifiers.append(mod)
    return obj, int(round(obj.active_cost)), int(round(obj.real_cost))
