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


__all__ = ["Limit", "LimitError", "PowerLevel"]
