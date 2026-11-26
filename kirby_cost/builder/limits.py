"""A campaign's power level, and the limits a build is held to.

The builder's fifth layer (character-workshop spec §5.2). A GM sets a power
level: the template, the points, and a few ceilings -- Active Points per
power, Damage Classes, SPD, defences. Whether a build is inside them is a
RULE, so it lives here, measured by the engine, and is never left to whoever
reviews the build: a reviewer judging "is 75 AP under 60" by eye is the
stale-number failure the engine exists to end.

The limit VALUES are the GM's, not the book's. What each kind measures is the
book's, and each measurement cites the passage defining its quantity.

`Limit.Kind` is a closed set, so a campaign cannot state a limit nothing
measures. OCV, DCV and SPD are 6E characteristics, so their caps are
`CHARACTERISTIC_MAX` limits naming the characteristic.

NO DEFAULTS: every field is required; ``limits=()`` says "no limits".

Grounds. A GM may limit Active Points in attacks, amount of defence and of
Resistant Defence, Combat Values, Damage Classes, DEX, INT and SPD (6E2 273,
pointing to the Character Ability Guidelines table, 6E1 35); a ceiling on
effect rather than points -- DCs, SPD, CV, defences -- is an Effectiveness
Ceiling (6E2 285). Each kind's measure cites the passage defining what it
measures.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from kirby_cost.builder.new import Template
from kirby_cost.builder.reachable import AddedDamage
from kirby_cost.engine.damage import (
    BOOK_DAMAGE_ADVANTAGES, DamageAdvantage, damage_classes_of,
)


class LimitError(ValueError):
    """A power level or limit that cannot be held to, named."""


@dataclass(frozen=True)
class Limit:
    """One ceiling a build may not exceed. ``maximum`` is inclusive: a
    build AT the limit is inside it."""

    class Kind(Enum):
        ACTIVE_POINTS = "active_points"
        DAMAGE_CLASSES = "damage_classes"
        CHARACTERISTIC_MAX = "characteristic_max"
        PD = "pd"
        ED = "ed"
        RESISTANT_PD = "resistant_pd"
        RESISTANT_ED = "resistant_ed"

    kind: "Limit.Kind"
    maximum: int
    #: The characteristic's XMLID for CHARACTERISTIC_MAX; None for any other kind.
    characteristic: str | None
    #: For DAMAGE_CLASSES, the Advantages that count toward an attack's DCs
    #: -- the GM's call (6E2 100); `BOOK_DAMAGE_ADVANTAGES` is the book's
    #: typical list, () counts none. None for any other kind.
    counts: tuple[DamageAdvantage, ...] | None
    #: For DAMAGE_CLASSES, whether 6E2 101's doubling guideline binds ("unless
    #: he rules otherwise, a character cannot more than double the Damage
    #: Classes of his base attack") -- the GM's call. None for any other kind.
    doubling: bool | None
    #: For DAMAGE_CLASSES, the Adding Damage methods the ceiling counts
    #: (6E2 101; 6E2 285 leaves it to the GM); () counts none, which measures
    #: each purchase by itself. None for any other kind.
    adders: tuple[AddedDamage, ...] | None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, Limit.Kind):
            raise LimitError(f"a limit's kind is a Limit.Kind, not {self.kind!r}")
        if isinstance(self.maximum, bool) or not isinstance(self.maximum, int) \
                or self.maximum < 0:
            raise LimitError(
                f"{self.kind.name}: maximum must be a whole number >= 0, "
                f"not {self.maximum!r}")
        if self.kind is Limit.Kind.CHARACTERISTIC_MAX:
            if not self.characteristic:
                raise LimitError(
                    "CHARACTERISTIC_MAX needs a characteristic (an XMLID, "
                    "e.g. 'SPD')")
            object.__setattr__(self, "characteristic",
                               self.characteristic.upper())
        elif self.characteristic is not None:
            raise LimitError(
                f"{self.kind.name} takes no characteristic, "
                f"got {self.characteristic!r}")
        if self.kind is Limit.Kind.DAMAGE_CLASSES:
            if not isinstance(self.counts, tuple) or not all(
                    isinstance(a, DamageAdvantage) for a in self.counts):
                raise LimitError(
                    "DAMAGE_CLASSES needs the Advantages that count toward "
                    "DCs, a tuple of DamageAdvantage (BOOK_DAMAGE_ADVANTAGES "
                    "is 6E2 100's typical list; () counts none)")
            if not isinstance(self.doubling, bool):
                raise LimitError(
                    "DAMAGE_CLASSES needs doubling stated, True or False: "
                    "whether 6E2 101's doubling guideline binds")
            if not isinstance(self.adders, tuple) or not all(
                    isinstance(a, AddedDamage) for a in self.adders):
                raise LimitError(
                    "DAMAGE_CLASSES needs the Adding Damage methods it counts, "
                    "a tuple of AddedDamage (6E2 101; () counts none)")
            if len(set(self.adders)) != len(self.adders):
                raise LimitError("an Adding Damage method is named twice")
        else:
            for field in ("counts", "doubling", "adders"):
                if getattr(self, field) is not None:
                    raise LimitError(
                        f"{self.kind.name} takes no {field}, got "
                        f"{getattr(self, field)!r}")

    @property
    def key(self) -> tuple["Limit.Kind", str | None]:
        """What makes two limits the same limit."""
        return self.kind, self.characteristic

    @property
    def label(self) -> str:
        return (self.characteristic if self.kind is Limit.Kind.CHARACTERISTIC_MAX
                else self.kind.name)


@dataclass(frozen=True)
class PowerLevel:
    """What a campaign builds characters at: the template, the points, and
    the limits (which may be none, but are stated)."""

    template: Template
    base_points: int
    disad_points: int
    experience: int
    limits: tuple[Limit, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.template, Template):
            raise LimitError(
                f"a power level's template is a Template, not {self.template!r}")
        for field in ("base_points", "disad_points", "experience"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise LimitError(f"{field} must be a whole number >= 0, "
                                 f"not {value!r}")
        if not isinstance(self.limits, tuple):
            raise LimitError("limits must be a tuple of Limit (() for none), "
                             f"not {type(self.limits).__name__}")
        seen: set = set()
        for limit in self.limits:
            if not isinstance(limit, Limit):
                raise LimitError(f"not a Limit: {limit!r}")
            if limit.key in seen:
                raise LimitError(f"{limit.label} is limited twice; state it once")
            seen.add(limit.key)


def _measured_purchases(hero):
    """Every purchase in powers and equipment that a per-power ceiling
    measures: each framework slot by itself, the framework never.

    A Multipower, VPP or Elemental Control is a pool of points, not a power
    (its slots are what is used), so a cap "per power" binds the slots. A
    Compound Power is one power made of parts, and is measured whole. Slots
    sit flat in the section with ``parent`` naming their framework, so the
    walk is one level: skip the `List` containers, keep everything else.
    """
    from kirby_cost.objects.list import List

    for section in ("powers", "equipment"):
        for obj in getattr(hero, section, None) or []:
            if not isinstance(obj, List):
                yield obj


def _active_points(hero, limit, doc, template_provider):
    """Active Points per power: the total cost after Adders and Advantages,
    before Limitations (6E1 121) -- the engine's oracle-verified
    ``active_cost``."""
    for obj in _measured_purchases(hero):
        yield str(obj.id), "Active Points", obj.active_cost


def _characteristic(hero, limit, doc, template_provider):
    """A characteristic's value as the character fights: in his Hero
    identity, so a purchase bought Only In Hero ID counts (`model.activation`).
    OCV, DCV and SPD are 6E characteristics and are capped this way (6E2 273
    names Combat Values, DEX, INT and SPD among the things a GM limits).

    A characteristic the build does not have (SPD on a Base6E) is refused
    by name: measuring it as 0 would pass any cap. What the build HAS is
    read off the build itself, never off the template it names -- a name
    the provider cannot resolve ("" included) falls back to Main6E, whose
    list has SPD."""
    from kirby_cost.model.activation import ActivationContext

    held = {c.xmlid for c in hero.characteristics}
    if limit.characteristic not in held:
        raise LimitError(
            f"{limit.characteristic} is limited, but this build (template "
            f"{doc['template']!r}) has no {limit.characteristic}")
    yield None, limit.characteristic, hero.temporal_characteristic(
        limit.characteristic, ActivationContext(in_hero_id=True))


def _defence(xmlid, resistant):
    """A defence measure: a character's PD (or ED) is his natural defence
    supplemented by defences bought as Powers, Resistant Protection among
    them; Resistant Defense is the part of it that also stops Killing BODY
    (6E2 105; 6E1 26).

    Read through the functions HD's own sheet is rendered from
    (`DefenseCharacteristic.nonresistant_total` -- HD's name for the WHOLE
    figure, resistant part included -- and ``resistant_total``), so the cap
    and the sheet cannot disagree. HD gives each a primary and a secondary
    figure (a purchase may affect only the secondary); a cap binds the
    character's best defence, so the larger is measured."""
    label = f"resistant {xmlid}" if resistant else xmlid

    def measure_(hero, limit, doc, template_provider):
        found = [c for c in hero.characteristics if c.xmlid == xmlid]
        if not found:
            raise LimitError(
                f"{label} is limited, but a build on {doc['template']} "
                f"has no {xmlid}")
        (ch,) = found
        read = ch.resistant_total if resistant else ch.nonresistant_total
        yield None, label, max(read(True, hero), read(False, hero))

    return measure_


def _parts(obj):
    """A purchase, or -- for a Compound Power -- each of its parts: every
    attack in a compound is its own attack, at its own Damage Classes."""
    parts = getattr(obj, "powers", None) or []
    if parts:
        for part in parts:
            yield from _parts(part)
    else:
        yield obj


def _damage_classes(hero, limit, doc, template_provider):
    """Damage Classes per attack, at the most each can reach under the
    Adding Damage methods the limit counts (6E2 101-104;
    `builder.reachable`, workshop spec §5.2.1). Measured in
    `measure_all`, which also reports what the build's words cannot
    settle; this entry keeps the kind in `_MEASURES`."""
    from kirby_cost.builder.reachable import reach

    reached, _ = reach(hero, limit)
    for r in reached:
        yield r.hd_id, r.describe(), r.dcs


_MEASURES = {
    Limit.Kind.ACTIVE_POINTS: _active_points,
    Limit.Kind.DAMAGE_CLASSES: _damage_classes,
    Limit.Kind.CHARACTERISTIC_MAX: _characteristic,
    Limit.Kind.PD: _defence("PD", False),
    Limit.Kind.ED: _defence("ED", False),
    Limit.Kind.RESISTANT_PD: _defence("PD", True),
    Limit.Kind.RESISTANT_ED: _defence("ED", True),
}


def measure(hero, limit: Limit, doc: dict, *, template_provider):
    """``(hd_id, what, measured)`` for each thing ``limit`` measures on
    ``hero`` (the loaded ``doc``). ``hd_id`` is None for a whole-character
    measure. A kind with no measure raises: it is never skipped."""
    try:
        fn = _MEASURES[limit.kind]
    except KeyError:
        raise LimitError(
            f"{limit.kind.name}: no measure for this kind yet") from None
    return list(fn(hero, limit, doc, template_provider))


def measure_all(hero, doc: dict, limits: tuple, *, template_provider):
    """The OVER_LIMIT problems for ``limits`` on ``hero``. A measure AT its
    maximum is inside it."""
    from kirby_cost.builder.verdict import Problem

    if not isinstance(limits, tuple):
        raise LimitError("limits must be a tuple of Limit (() for none), "
                         f"not {type(limits).__name__}")
    problems = []
    for limit in limits:
        if not isinstance(limit, Limit):
            raise LimitError(f"not a Limit: {limit!r}")
        if limit.kind is Limit.Kind.DAMAGE_CLASSES:
            from kirby_cost.builder.reachable import reach

            reached, unmeasured = reach(hero, limit)
            for r in reached:
                if r.dcs > limit.maximum:
                    problems.append(Problem(
                        Problem.Kind.OVER_LIMIT, r.hd_id, None,
                        f"{r.describe()}; the limit is {limit.maximum}"))
            problems.extend(Problem(Problem.Kind.UNMEASURED, u.hd_id, None, u.detail)
                            for u in unmeasured)
            continue
        for hd_id, what, measured in measure(
                hero, limit, doc, template_provider=template_provider):
            if measured > limit.maximum:
                problems.append(Problem(
                    Problem.Kind.OVER_LIMIT, hd_id, None,
                    f"{what} {measured:g}; the limit is {limit.maximum}"))
    return problems


__all__ = ["AddedDamage", "BOOK_DAMAGE_ADVANTAGES", "DamageAdvantage", "Limit", "LimitError",
           "PowerLevel", "measure", "measure_all"]
