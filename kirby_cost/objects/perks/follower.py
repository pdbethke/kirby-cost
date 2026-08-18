"""
Follower Perk.

Converted from com.hero.objects.perks.Follower.java
"""

from typing import Optional
from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.util.rounder import round_half_down


class Follower(Perk, xmlid="FOLLOWER"):
    """Follower perk - companion NPC."""

    #: OVERCOST/OVERVAL/MULTIPLIERCOST/MULTIPLIERVAL come from the TEMPLATE —
    #: the Python comment below said so and the writer stated them anyway, so
    #: 15 characters had a template default frozen into their file as a
    #: per-character override. Java writes only NUMBER, BASEPOINTS,
    #: DISADPOINTS and FILE_ASSOCIATION (Follower.getSaveXML); declared here, the
    #: writer's "the source did not state it and nothing changed it" rule keeps
    #: the other four out on its own, without a second hand-written list to
    #: remember them by.
    XML_ATTRS = (
        XMLAttr("NUMBER", "multiples", "int"),
        XMLAttr("BASEPOINTS", "_base_points", "int"),
        XMLAttr("DISADPOINTS", "_disad_points", "int"),
        XMLAttr("OVERCOST", "over_cost", "int"),
        XMLAttr("OVERVAL", "over_val", "int"),
        XMLAttr("MULTIPLIERCOST", "multiplier_cost", "int"),
        XMLAttr("MULTIPLIERVAL", "multiplier_val", "int"),
        XMLAttr("FILE_ASSOCIATION", "file_path", omit_if=None),
    )

    def __init__(self, element=None):
        """Initialize Follower perk."""
        # Set defaults BEFORE super().__init__ which triggers _init()
        self.over_cost: int = 0
        self.over_val: int = 1
        self.multiplier_cost: int = 5
        self.multiplier_val: int = 2
        self.multiples: int = 1
        self._base_points: int = 0
        self._disad_points: int = 0
        self.file_path: Optional[str] = None
        super().__init__(element, "FOLLOWER")

    def _init(self, element) -> None:
        """Java Follower.init() defaults, before the document is read."""
        self._display = "Follower"
        self._alias = "Follower"
        self._base_cost = 0.0
        self._level_cost = 1.0
        self._level_value = 5.0
        self._minimum_cost = 1.0
        self._max_cost = 10.0
        super()._init(element)

    @property
    def base_points(self) -> int:
        return self._base_points

    @property
    def disad_points(self) -> int:
        return self._disad_points

    @property
    def total_cost(self) -> float:
        """
        Calculate follower cost.

        Cost = basePoints/levelValue * levelCost + multiples cost + adders.
        For 6E, always uses simple base points / level value formula.

        Ported from Follower.java getTotalCost().
        """
        self.enhancer_applied = None
        d = self.base_cost

        # Calculate follower point cost
        # In 6E, always use simple formula (assume 6E for now)
        d += float(self.base_points) / self._level_value * self._level_cost if self._level_value != 0 else 0.0

        # Multiples cost (5 per doubling by default)
        n = 0
        d2 = float(self.multiples)
        while d2 > 1.0:
            d2 /= float(self.multiplier_val)
            n += 1
        d += float(n * self.multiplier_cost)

        # Positive adders
        for adder in self.assigned_adders:
            if adder.real_cost > 0.0:
                d += adder.real_cost

        d = round_half_down(d)

        # Min/max clamp
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        elif d > self._max_cost and self.max_set:
            d = self._max_cost

        # Negative adders
        for adder in self.assigned_adders:
            if adder.real_cost < 0.0:
                d += adder.real_cost

        return d

