"""Enraged — a complication that leads with the word it is really about."""

from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.disads.disadvantage import Disadvantage


class Enraged(Disadvantage):
    """Enraged / Berserk.

    HD prints ``Enraged:  Berserk in combat or when injured (Very Common),
    go 11-, recover 11-``. The word "Berserk" comes from an ADDER, and it is
    printed BEFORE the trigger text rather than in its place among the other
    adders — so Enraged is the one complication whose input does not follow
    its modifiers.

    Printing it early is only half of it: HD then clears the adder's
    displayInString flag so the adder loops skip it, which is why this class
    is also the one that honours that flag.
    """

    _honours_display_in_string = True
    _input_after_modifiers = False

    def __init__(self, element=None):
        super().__init__()
        self.xmlid = "ENRAGED"
        if element is not None:
            self._init(element)

    def _column2_head(self) -> str:
        if not (self.input and self.input.strip()):
            return ""
        out = ""
        berserk = GenericObject.find_object_by_id(self.assigned_adders, "BERSERK")
        if berserk is not None:
            berserk.display_in_string = False
            out += " " + berserk.alias
        return out + " " + self.input
