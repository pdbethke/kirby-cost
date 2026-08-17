"""TemplateProvider — source-agnostic access to HERO System template data.

Any class that implements ``get_template_data(xmlid)`` can serve as a provider.
kirby-cost ships one implementation, ``HDTTemplateProvider``, which reads the
user's own HERO Designer ``.hdt``; the package carries no template data of its
own. A consumer that keeps templates in its own storage (kirby-api's relational
catalogue, say) implements this protocol against that storage and passes the
provider in.

``HDCLoader`` accepts an optional provider at construction time and falls back
to ``HDTTemplateProvider`` — which resolves a ``.hdt`` from its argument or
``KIRBY_COST_HDT`` — when none is given.

A provider may also implement ``get_adder_type_map()``, returning
``xmlid -> types`` for every adder in the template including nested ones. The
loader uses it where a type decides a cost (Transport Familiarity's Riding
discount) and treats its absence as "no types known".

It may also implement ``get_maneuver(display)``. Maneuvers are the one thing a
template does not name by xmlid — ``<MANEUVER DISPLAY="Killing Strike">`` has
no XMLID attribute, and every HDC maneuver is written ``XMLID="MANEUVER"`` —
so Java matches them on display (``Hero.java:2706-2731``) and the loader asks
for them that way. A provider without the method serves no maneuvers, and
every maneuver then costs whatever its own HDC element states, which is the
custom-maneuver path.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from kirby_cost.template.dataclasses import TemplateData


# ── Protocol ─────────────────────────────────────────────────────────────────

@runtime_checkable
class TemplateProvider(Protocol):
    """Minimal interface expected by HDCLoader."""

    def get_template_data(self, xmlid: str) -> Optional[TemplateData]:
        """Return a TemplateData for *xmlid*, or None if unknown."""
        ...
