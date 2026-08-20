"""
Force Wall power class for kirby-cost.

Converted from com.hero.objects.powers.ForceWall.java

Power to create force walls.
"""

from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.powers.power import Power


class ForceWall(Power, xmlid="FORCEWALL"):
    """
    Force Wall power.

    Creates a wall of force with DEF and BODY.
    """

    #: A wall is its dimensions and its defenses, and it had neither on the way
    #: back out. ``_init`` read the six dimension attributes and never the four
    #: defence ones, so PDLEVELS/EDLEVELS/MDLEVELS/POWDLEVELS stayed 0 through
    #: a whole round trip — 54 walls in the corpus reloaded undefended. Meanwhile
    #: ``get_save_xml`` wrote COSTPERINCH and COSTPERBODY unconditionally, so a
    #: file that never stated them got them anyway, turning a template default
    #: into a per-character override. Declared once, both directions agree; see
    #: ForceField, which already carries the same four.
    XML_ATTRS = (
        XMLAttr("PDLEVELS", "pd_levels", "int"),
        XMLAttr("EDLEVELS", "ed_levels", "int"),
        XMLAttr("MDLEVELS", "md_levels", "int"),
        XMLAttr("POWDLEVELS", "powd_levels", "int"),
        XMLAttr("LENGTHLEVELS", "length_levels", "int"),
        XMLAttr("HEIGHTLEVELS", "height_levels", "int"),
        XMLAttr("BODYLEVELS", "body_levels", "int"),
        XMLAttr("WIDTHLEVELS", "width_levels", "float"),
        XMLAttr("COSTPERINCH", "cost_per_inch", "int"),
        XMLAttr("COSTPERBODY", "cost_per_body", "int"),
    )

    def to_build_dict(self) -> dict:
        d = super().to_build_dict()
        for field in ("length_levels", "height_levels", "body_levels",
                      "width_levels"):
            if getattr(self, field, 0):
                d[field] = getattr(self, field)
        # Always emitted so total_cost reproduces: the wall's level cost reads
        # these, and their defaults are not what every wall carries.
        d["cost_per_inch"] = getattr(self, "cost_per_inch", 2)
        d["cost_per_body"] = getattr(self, "cost_per_body", 1)
        return d

    
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
        """Empty. Java's ``ForceWall.getDamageDisplay`` returns "".

        The numbers this power is about — its defences and dimensions, or its
        END and REC — are written by column2_output itself, so a damage
        display that also produced them printed them twice.
        """
        return ""
    @property
    def column2_output(self) -> str:
        """``Barrier 10 PD/6 ED, 8 BODY (up to 12m long, 4m tall, and 1m thick)``.

        Ported from ``ForceWall.getColumn2Output`` (6E branch). A barrier is
        defined by its defences AND its dimensions, and the dimensions were
        missing entirely — the part of the sentence that says how much wall
        there is.
        """
        ret = f"{self.alias or ''} {self.damage_display}"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        ret = ret.strip() + " "

        added = False
        for levels, label in ((self.pd_levels, "PD"), (self.ed_levels, "ED"),
                              (self.md_levels, "Mental Defense"),
                              (getattr(self, "powd_levels", 0), "Power Defense")):
            if levels and levels > 0:
                if added:
                    ret += "/"
                ret += f"{levels} {label}"
                added = True
        ret = ret.strip()

        # A barrier's dimensions are LEVELS above a one-metre minimum, and
        # half a metre thick before any width is bought — the "+1" and the
        # "+.5" are the wall you get for free.
        length = self.length_levels + 1
        height = self.height_levels + 1
        width = self.width_levels + 0.5
        ret += f", {self.body} BODY"
        ret += (f" (up to {length}m long, {height}m tall, "
                f"and {_fraction(width)}m thick)")
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret


def _fraction(value: float) -> str:
    """``1``, ``1/2``, ``1 1/2`` — a barrier's thickness as HD writes it."""
    whole = int(value)
    rest = value - whole
    frac = {0.25: "1/4", 0.5: "1/2", 0.75: "3/4"}.get(round(rest, 2), "")
    if not frac:
        return str(whole)
    return f"{whole} {frac}" if whole else frac
