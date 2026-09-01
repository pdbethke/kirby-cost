"""Which purchases count right now — and the derivation that says why.

A characteristic has a BASE (what the sheet says, what costs derive from) and
a TEMPORAL value (what is true this Phase). This module holds the pieces that
turn one into the other.

The derivation matters as much as the number. A log line reading
"DEX 19 = 10 base + 9 (Enhanced Reflexes, Hero ID)" is debuggable; a bare 19
is not, and a bare 19 is why two code paths disagreed for months without
anyone noticing.

v1 knows exactly one condition: a purchase limited to the character's Hero
identity (the OIHID limitation). Focus limitations, charges and activation
rolls fit the same shape and are deliberately NOT implemented — one condition,
built so a second is cheap.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from kirby_cost.objects.base import GenericObject


@dataclass(frozen=True)
class ActivationContext:
    """What is true about this character right now.

    Defaults to being in the Hero identity: a character in a fight is
    overwhelmingly in costume, and defaulting the other way would silently
    weaken everyone whose abilities are bought that way.
    """

    in_hero_id: bool = True


@dataclass(frozen=True)
class Contribution:
    """One thing adding to (or subtracting from) a characteristic.

    `source_label` is what the derivation prints, so it should name the thing
    a reader would recognise on the character sheet.
    """

    xmlid: str
    delta: float
    source_label: str
    requires_hero_id: bool = False

    def applies(self, ctx: ActivationContext) -> bool:
        if self.requires_hero_id and not ctx.in_hero_id:
            return False
        return True


@dataclass(frozen=True)
class CharacteristicState:
    """A characteristic as a whole: its base, and everything acting on it.

    This is the object the engine lacked. Purchases had a class; the
    characteristic itself did not, so nothing could answer "what is it, and
    why".
    """

    xmlid: str
    base: float
    contributions: list[Contribution] = field(default_factory=list)

    def active(self, ctx: ActivationContext) -> list[Contribution]:
        return [c for c in self.contributions if c.applies(ctx)]

    def value(self, ctx: ActivationContext) -> float:
        return self.base + sum(c.delta for c in self.active(ctx))

    def derivation(self, ctx: ActivationContext) -> str:
        parts = [f"{self.base:g} base"]
        parts += [f"{c.delta:+g} ({c.source_label})" for c in self.active(ctx)]
        return f"{self.xmlid} {self.value(ctx):g} = " + " ".join(parts)


def _has_hero_id_limitation(obj) -> bool:
    """True if ``obj`` carries the Only-In-Hero-ID limitation (xmlid OIHID).

    Uses ``GenericObject.find_object_by_id``, the engine's own idiom for
    locating an assigned modifier by xmlid (see e.g.
    ``kirby_cost/objects/base.py``'s ``duration`` property, which builds
    ``has``/``has_own`` closures around exactly this call). It recurses
    through List/CompoundPower containers, unlike a hand-rolled scan.
    """
    return GenericObject.find_object_by_id(
        getattr(obj, "assigned_modifiers", None) or [], "OIHID"
    ) is not None


def contribution_from_purchase(obj) -> "Contribution | None":
    """Describe what a purchased object contributes to a characteristic.

    Returns None when the object contributes nothing — it is not a
    characteristic purchase, or it buys no levels.

    The Hero-identity limitation is xmlid ``OIHID`` in the HD model.
    """
    xmlid = (getattr(obj, "xmlid", None) or "").upper()
    if not xmlid:
        return None
    levels = float(getattr(obj, "levels", 0) or 0)
    if levels == 0:
        return None
    name = (getattr(obj, "name", None) or "").strip()
    return Contribution(
        xmlid=xmlid,
        delta=levels,
        source_label=name or xmlid,
        requires_hero_id=_has_hero_id_limitation(obj),
    )
