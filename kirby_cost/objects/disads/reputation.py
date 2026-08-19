"""Negative Reputation — the complication, not the Perk of the same name."""

from kirby_cost.objects.disads.disadvantage import Disadvantage


class Reputation(Disadvantage):
    """Negative Reputation.

    ``Negative Reputation:  terrifying powerful evil creature, Very
    Frequently (Extreme)``. Two things separate it from the generic
    complication:

    A comma before the first adder, where every other complication uses a
    space — the frequency reads as a clause about the reputation rather than
    part of its description.

    And brackets MERGE rather than nest. Its adders' aliases deliberately
    open a bracket they never close — ``ALIAS="(Extreme"`` — so that the
    renderer closes them all at the end. When a second such adder arrives
    while one is already open, HD joins them with "; " inside the existing
    bracket and drops the newcomer's "(", giving "(Extreme; Known Only To A
    Small Group)" rather than two nested brackets.

    Note this is NOT the Perk called Reputation. They share an xmlid and have
    different adders, and the template index is first-wins — see
    ``_template_section`` in the loader.
    """

    _first_required_sep = ", "
    _merges_brackets = True

    def __init__(self, element=None):
        super().__init__()
        self.xmlid = "REPUTATION"
        if element is not None:
            self._init(element)
