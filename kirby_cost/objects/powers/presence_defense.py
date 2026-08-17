"""
Presence Defense power class for kirby-cost.

6E1 p249: 1 Character Point per 1 point of Presence Defense. Reduces
incoming Presence Attack dice as if it were Resistant Defense vs PRE.
"""

from kirby_cost.objects.powers.power import Power


class PresenceDefense(Power, xmlid="PRESENCEDEFENSE"):
    """
    Presence Defense power.

    Defense against Presence Attacks (6E1 p249). Sibling of
    MentalDefense / PowerDefense / FlashDefense — same shape, same
    1-point-per-level cost basis.
    """

    def __init__(self):
        super().__init__()
        self.xmlid = PresenceDefense.XMLID
        self._duration = "CONSTANT"

    @property
    def damage_display(self) -> str:
        return f"{self._levels} points"
