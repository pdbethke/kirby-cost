"""
Vehicle Perk.

Converted from com.hero.objects.perks.Vehicle.java
"""

from typing import Optional
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.util.rounder import round_half_down


class Vehicle(Perk, xmlid="VEHICLE_BASE"):
    """Vehicle/Base perk - vehicles and bases built on points."""

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

    def _init(self, element) -> None:
        """Initialize from XML, including vehicle-specific fields."""
        super()._init(element)
        if element is None:
            return
        from kirby_cost.io.xml_utility import XMLUtility

        for attr, field, conv in [
            ("BASEPOINTS", "_base_points", lambda v: int(float(v))),
            ("DISADPOINTS", "_disad_points", lambda v: int(float(v))),
            ("NUMBER", "multiples", int),
            ("OVERCOST", "over_cost", int),
            ("OVERVAL", "over_val", int),
            ("MULTIPLIERCOST", "multiplier_cost", int),
            ("MULTIPLIERVAL", "multiplier_val", int),
        ]:
            val = XMLUtility.get_value(element, attr)
            if val:
                try:
                    setattr(self, field, conv(val))
                except (ValueError, TypeError):
                    pass

    def get_save_xml(self):
        """Serialize vehicle including vehicle-specific fields."""
        element = self.get_general_save_xml()
        element.set("BASEPOINTS", str(self._base_points))
        element.set("DISADPOINTS", str(self._disad_points))
        element.set("NUMBER", str(self.multiples))
        element.set("OVERCOST", str(self.over_cost))
        element.set("OVERVAL", str(self.over_val))
        element.set("MULTIPLIERCOST", str(self.multiplier_cost))
        element.set("MULTIPLIERVAL", str(self.multiplier_val))
        return element

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
