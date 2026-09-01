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
