"""
Follower Perk.

Converted from com.hero.objects.perks.Follower.java
"""

from typing import Optional
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.util.rounder import round_half_down


class Follower(Perk, xmlid="FOLLOWER"):
    """Follower perk - companion NPC."""

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
        """Initialize from XML, including follower-specific fields.

        Mirrors Java Follower.init() + restoreFromSave() which read
        OVERCOST, OVERVAL, MULTIPLIERCOST, MULTIPLIERVAL from the template
        definition and NUMBER, BASEPOINTS, DISADPOINTS from saved data.
        """
        # Set Java init() defaults
        self._display = "Follower"
        self._alias = "Follower"
        self._base_cost = 0.0
        self._level_cost = 1.0
        self._level_value = 5.0
        self._minimum_cost = 1.0
        self._max_cost = 10.0
        super()._init(element)
        if element is None:
            return
        from kirby_cost.io.xml_utility import XMLUtility

        # Template-level attributes (Java init())
        for attr, field, conv in [
            ("OVERCOST", "over_cost", int),
            ("OVERVAL", "over_val", int),
            ("MULTIPLIERCOST", "multiplier_cost", int),
            ("MULTIPLIERVAL", "multiplier_val", int),
        ]:
            val = XMLUtility.get_value(element, attr)
            if val and val.strip():
                try:
                    setattr(self, field, conv(val))
                except (ValueError, TypeError):
                    pass

        # Saved character data (Java restoreFromSave())
        for attr, field, conv in [
            ("NUMBER", "multiples", int),
            ("BASEPOINTS", "_base_points", lambda v: int(float(v))),
            ("DISADPOINTS", "_disad_points", lambda v: int(float(v))),
        ]:
            val = XMLUtility.get_value(element, attr)
            if val and val.strip():
                try:
                    setattr(self, field, conv(val))
                except (ValueError, TypeError):
                    pass

    def get_save_xml(self):
        """Serialize follower including follower-specific fields."""
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

