"""Susceptibility — the complication that never counts its adders."""

from kirby_cost.objects.disads.disadvantage import Disadvantage


class Susceptibility(Disadvantage):
    """Susceptibility.

    ``Susceptibility:  to holy places and objects, takes 2d6 damage per
    Phase``: "per Phase" attaches to the damage with a space, not a comma.

    Two of HD's differences here produce that one effect and it is worth
    naming both, because either alone would be wrong. The separators are
    swapped — the first adder takes ", " and the rest " " — and the adder
    counter is never advanced, so the "first adder" branch cannot fire at
    all and every adder takes the space.
    """

    _counts_adders = False
    _first_adder_sep = ", "
    _later_adder_sep = " "

    def __init__(self, element=None):
        super().__init__()
        self.xmlid = "SUSCEPTIBILITY"
        if element is not None:
            self._init(element)
