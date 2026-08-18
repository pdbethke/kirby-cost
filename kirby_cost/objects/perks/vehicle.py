"""
Vehicle Perk.

Converted from com.hero.objects.perks.Vehicle.java
"""

from typing import Optional
from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.util.rounder import round_half_down


class Vehicle(Perk, xmlid="VEHICLE_BASE"):
    """Vehicle/Base perk - vehicles and bases built on points."""

    #: OVERCOST/OVERVAL/MULTIPLIERCOST/MULTIPLIERVAL come from the TEMPLATE —
    #: the Python comment below said so and the writer stated them anyway, so
    #: 12 characters had a template default frozen into their file as a
    #: per-character override. Java writes only NUMBER, BASEPOINTS,
    #: DISADPOINTS and FILE_ASSOCIATION (Vehicle.getSaveXML); declared here, the
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
        """Initialize Vehicle perk."""
        super().__init__(element, "VEHICLE_BASE")
        self.over_cost: int = 1
        self.over_val: int = 1
        self.multiplier_cost: int = 5
        self.multiplier_val: int = 2
        self.multiples: int = 1
        self._base_points: int = 0
        self._disad_points: int = 0
        self.file_path: Optional[str] = None

    @property
    def base_points(self) -> int:
        return self._base_points

    @property
    def disad_points(self) -> int:
        return self._disad_points

    @property
    def total_cost(self) -> float:
        """
        Calculate vehicle/base cost.

        Cost = basePoints/levelValue * levelCost + multiples cost + adders.
        For 6E, always uses simple base points / level value formula.

        Ported from Vehicle.java getTotalCost().
        """
        self.enhancer_applied = None
        d = self.base_cost

        # Calculate vehicle/base point cost
        # In 6E, always use simple formula
        if self._level_value != 0:
            d += float(self.base_points) / self._level_value * self._level_cost

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
