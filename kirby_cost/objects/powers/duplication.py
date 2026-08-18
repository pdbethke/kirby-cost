"""
Duplication power class for kirby-cost.

Converted from com.hero.objects.powers.Duplication.java

Power to duplicate oneself.
"""

from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.powers.power import Power
from kirby_cost.io.xml_utility import XMLUtility
from typing import Optional


class Duplication(Power, xmlid="DUPLICATION"):
    """
    Duplication power.

    Creates duplicate versions of the character.
    """

    #: NUMBER and POINTS are the character's; OVERCOST, OVERVAL,
    #: MULTIPLIERCOST and MULTIPLIERVAL are the TEMPLATE's, and get_save_xml
    #: stated all six, freezing four template defaults into 6 characters'
    #: files as per-character overrides. Java writes NUMBER, POINTS and
    #: FILE_ASSOCIATION only (Duplication.getSaveXML). Declared, so the
    #: writer's own "the source did not state it and nothing changed it" rule
    #: keeps the template's four out without a second list to maintain.
    XML_ATTRS = (
        XMLAttr("NUMBER", "multiples", "int"),
        XMLAttr("POINTS", "points", "int"),
        XMLAttr("OVERCOST", "over_cost", "int"),
        XMLAttr("OVERVAL", "over_val", "int"),
        XMLAttr("MULTIPLIERCOST", "multiplier_cost", "int"),
        XMLAttr("MULTIPLIERVAL", "multiplier_val", "int"),
    )

    def __init__(self):
        """Initialize a Duplication power."""
        super().__init__()
        self.xmlid = Duplication.XMLID
        self._duration = "CONSTANT"
        self.over_cost: int = 1
        self.over_val: int = 1
        self.multiplier_cost: int = 5
        self.multiplier_val: int = 2
        self.multiples: int = 1
        self.points: int = 0
        self.file_path: Optional[str] = None
        self.file_association_last_check: Optional[int] = None

    def _init(self, element) -> None:
        """Java Duplication.init() defaults, before the document is read."""
        self._display = "Duplication"
        self._alias = "Duplication"
        self._base_cost = 0.0
        self._level_cost = 1.0
        self._level_value = 5.0
        self._minimum_cost = 1.0
        super()._init(element)

    @property
    def total_cost(self) -> float:
        """
        Calculate total cost for Duplication.

        Uses points (duplicate's point value) instead of levels.
        In 6E, always uses simple formula. Adds multiplier cost for
        multiple duplicates (5pts per doubling by default).

        Ported from Duplication.java getTotalCost().
        """
        self.enhancer_applied = None
        d = self.base_cost

        # 6E: simple points / levelValue * levelCost
        if self._level_value != 0.0:
            d += float(self.points) / self._level_value * self._level_cost

        # Multiples cost
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

        # Note: Java Duplication.getTotalCost() does NOT round, unlike
        # Follower which calls Rounder.roundHalfDown().

        # Min/max
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        elif d > self._max_cost and self.max_set:
            d = self._max_cost

        # Negative adders
        for adder in self.assigned_adders:
            if adder.real_cost < 0.0:
                d += adder.real_cost

        return d

    @property
    def damage_display(self) -> str:
        """Get duplication display."""
        return f"{self.multiples} duplicate{'s' if self.multiples != 1 else ''}"
    
    def clear_file_path(self) -> None:
        """Clear associated file path."""
        self.file_path = None
        self.file_association_last_check = None

