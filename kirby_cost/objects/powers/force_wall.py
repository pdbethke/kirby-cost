"""
Force Wall power class for kirby-cost.

Converted from com.hero.objects.powers.ForceWall.java

Power to create force walls.
"""

from kirby_cost.objects.powers.power import Power


class ForceWall(Power, xmlid="FORCEWALL"):
    """
    Force Wall power.
    
    Creates a wall of force with DEF and BODY.
    """
    
    def __init__(self):
        """Initialize a Force Wall power."""
        super().__init__()
        self.xmlid = ForceWall.XMLID
        self._duration = "CONSTANT"
        self.pd_levels: int = 0
        self.ed_levels: int = 0
        self.md_levels: int = 0
        self.powd_levels: int = 0
        self.length_levels: int = 0
        self.height_levels: int = 0
        self.width_levels: float = 0.0
        self.body_levels: int = 0
        self.cost_per_inch: int = 2   # Java default in ForceWall.init()
        self.cost_per_body: int = 1   # Java default (field initializer)

    def _init(self, element) -> None:
        """Initialize from XML, including dimension levels."""
        super()._init(element)
        if element is None:
            return
        from kirby_cost.io.xml_utility import XMLUtility

        for attr, field, conv in [
            ("LENGTHLEVELS", "length_levels", int),
            ("HEIGHTLEVELS", "height_levels", int),
            ("BODYLEVELS", "body_levels", int),
            ("WIDTHLEVELS", "width_levels", float),
            ("COSTPERINCH", "cost_per_inch", int),
            ("COSTPERBODY", "cost_per_body", int),
        ]:
            val = XMLUtility.get_value(element, attr)
            if val:
                try:
                    setattr(self, field, conv(val))
                except (ValueError, TypeError):
                    pass

    def get_save_xml(self):
        """Serialize force wall including dimension levels."""
        element = self.get_general_save_xml()
        element.set("LENGTHLEVELS", str(self.length_levels))
        element.set("HEIGHTLEVELS", str(self.height_levels))
        element.set("BODYLEVELS", str(self.body_levels))
        element.set("WIDTHLEVELS", str(self.width_levels))
        element.set("COSTPERINCH", str(self.cost_per_inch))
        element.set("COSTPERBODY", str(self.cost_per_body))
        return element

    @property
    def body(self) -> int:
        """Get BODY levels."""
        return self.body_levels
    
    @property
    def total_cost(self) -> float:
        """
        Calculate total cost for Force Wall.

        Adds length/height/width/body level costs to base power cost.
        In 6E: length and height cost half of costPerInch, width costs full.

        Ported from ForceWall.java getTotalCost().
        """
        d = super().total_cost

        # costPerInch and costPerBody are read from XML (defaults: 2 and 1)
        # matching Java ForceWall.init() / restoreFromSave()
        cost_per_inch = self.cost_per_inch
        cost_per_body = self.cost_per_body

        # 6E version (assume 6E) — matches Java ForceWall.getTotalCost()
        d += float(cost_per_inch // 2 * self.length_levels)
        d += float(cost_per_inch // 2 * self.height_levels)
        d += float(cost_per_inch) * self.width_levels
        d += float(cost_per_body * self.body_levels)

        return d

    @property
    def damage_display(self) -> str:
        """Get force wall display."""
        # Stub: would format DEF, BODY, dimensions
        return f"{self.pd_levels} PD/{self.ed_levels} ED, {self.body_levels} BODY"

