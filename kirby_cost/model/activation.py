"""Which purchases count right now — and the derivation that says why.

A characteristic has a BASE (what the sheet says, what costs derive from) and
a TEMPORAL value (what is true this Phase). This module holds the pieces that
turn one into the other.

The derivation matters as much as the number. A log line reading
"DEX 19 = 10 base + 9 (Enhanced Reflexes, Hero ID)" is debuggable; a bare 19
is not, and a bare 19 is why two code paths disagreed for months without
anyone noticing.

v1 knows exactly one condition: a purchase limited to the character's Hero
identity (the OIHID limitation, printed "Only In Alternate Identity"; the
Limitation is described at 6E1 p.386, and the book's own index names that
page). It restricts a power to one of the character's two identities, so a
character out of costume simply does not have it. Focus limitations, charges
and activation rolls fit the same shape and are deliberately NOT implemented —
one condition, built so a second is cheap.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_cost.model.modifiers import has_modifier


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
    contributions: tuple[Contribution, ...] = ()

    def __post_init__(self) -> None:
        # `frozen=True` freezes the ATTRIBUTE, not what it points at: with a
        # plain list, `state.contributions.append(...)` still mutated a
        # supposedly-immutable state. Callers hand in whatever sequence is
        # convenient (the hero builds a list), so coerce once, here.
        object.__setattr__(self, "contributions", tuple(self.contributions))

    def active(self, ctx: ActivationContext) -> list[Contribution]:
        return [c for c in self.contributions if c.applies(ctx)]

    def value(self, ctx: ActivationContext) -> float:
        return self.base + sum(c.delta for c in self.active(ctx))

    def derivation(self, ctx: ActivationContext) -> str:
        parts = [f"{self.base:g} base"]
        parts += [f"{c.delta:+g} ({c.source_label})" for c in self.active(ctx)]
        return f"{self.xmlid} {self.value(ctx):g} = " + " ".join(parts)


def _has_hero_id_limitation(obj) -> bool:
    """True if the Only-In-Hero-ID limitation (xmlid OIHID) binds ``obj``.

    Either because the purchase carries it or because something enclosing it
    does. Both rules — recursion through containers, and inheritance from an
    enclosing purchase minus its PRIVATE modifiers — now live in
    ``kirby_cost.model.modifiers``, which is also what kirby-combat asks, so
    the three copies of this walk that used to disagree are one.
    """
    return has_modifier(obj, "OIHID")


def _affects_the_characteristic(obj) -> bool:
    """True if HD counts this purchase toward the character's totals.

    ``AFFECTS_PRIMARY`` / ``AFFECTS_TOTAL`` are HD's own record of whether a
    purchase raises the character's characteristic or merely sits on the
    sheet as a situational ability, and they are written into every HDC
    element (``CharAffectingObject.XML_ATTRS``). Primary implies total, which
    is why this reads the ``affect_total`` property rather than the raw
    attribute — that property is the Java port's implication rule
    (``char_affecting.py``), not a convenience wrapper.

    This is the difference between two purchases that otherwise look
    identical to this module:

      * White Wolf's +30 STR is ``AFFECTS_TOTAL="Yes"``: it is part of his
        numbers, conditioned on being in costume. It contributes.
      * Gorgon's "Tail" +20 STR is ``AFFECTS_TOTAL="No"``, and its
        limitation is aliased "Only With Tail" — a restrainable limb, not a
        general increase. HD does not add it to his STR, and neither does
        this. Same for a Multipower slot like Ravel's "Reinforced String".

    A purchase HD excludes from the total is situational by construction,
    and the situation is exactly what v1 does not model. Counting it would
    hand every such character a permanent bonus the character sheet does
    not give them: measured, it made Gorgon STR 80 instead of 60 in every
    calculation, thrown-object damage included.

    Objects with no such flags (anything that is not a
    ``CharAffectingObject``) default to True, matching the class default.
    """
    return bool(getattr(obj, "affect_total", True))


def contribution_from_purchase(obj) -> "Contribution | None":
    """Describe what a purchased object contributes to a characteristic.

    Returns None when the object contributes nothing — it is not a
    characteristic purchase, it buys no levels, or HD does not count it
    toward the character's total (see ``_affects_the_characteristic``).

    The Hero-identity limitation is xmlid ``OIHID`` in the HD model.
    """
    xmlid = (getattr(obj, "xmlid", None) or "").upper()
    if not xmlid:
        return None
    levels = float(getattr(obj, "levels", 0) or 0)
    if levels == 0:
        return None
    if not _affects_the_characteristic(obj):
        return None
    name = (getattr(obj, "name", None) or "").strip()
    return Contribution(
        xmlid=xmlid,
        delta=levels,
        source_label=name or xmlid,
        requires_hero_id=_has_hero_id_limitation(obj),
    )
