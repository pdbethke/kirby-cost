"""A campaign's power level, and the limits a build is held to.

The builder's fifth layer (character-workshop spec §5.2). A GM sets a power
level: the template, the points, and a few ceilings -- Active Points per
power, Damage Classes, SPD, defences. Whether a build is inside them is a
RULE, so it lives here, measured by the engine, and not in a critic's prompt:
a model checking "is 75 AP under 60" is the stale-number failure the
workshop exists to end.

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

    A characteristic the build's template does not have (SPD on a Base6E)
    is refused by name: measuring it as 0 would pass any cap."""
    from kirby_cost.model.activation import ActivationContext

    template = doc["template"]
    held = template_provider.for_template(template).characteristics()
    if limit.characteristic not in held:
        raise LimitError(
            f"{limit.characteristic} is limited, but a build on {template} "
            f"has no {limit.characteristic}")
    yield None, limit.characteristic, hero.temporal_characteristic(
        limit.characteristic, ActivationContext(in_hero_id=True))


_MEASURES = {
    Limit.Kind.ACTIVE_POINTS: _active_points,
    Limit.Kind.CHARACTERISTIC_MAX: _characteristic,
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
        for hd_id, what, measured in measure(
                hero, limit, doc, template_provider=template_provider):
            if measured > limit.maximum:
                problems.append(Problem(
                    Problem.Kind.OVER_LIMIT, hd_id, None,
                    f"{what} {measured:g}; the limit is {limit.maximum}"))
    return problems


__all__ = ["Limit", "LimitError", "PowerLevel", "measure", "measure_all"]
