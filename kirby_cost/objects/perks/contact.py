"""
Contact Perk.

Converted from com.hero.objects.perks.Contact.java

Cost is fully template-driven (base + levels * level_cost + adders); the Java
class adds no special cost logic. It only overrides display output and the
Contact roll, both of which we mirror here for fidelity.
"""

from kirby_cost.objects.perks.perk import Perk


class Contact(Perk, xmlid="CONTACT"):
    """Contact perk - NPC helper. Cost inherited from the base Perk/template."""

    def __init__(self, element=None):
        """Initialize Contact perk."""
        super().__init__(element, self.XMLID)

    @property
    def roll(self) -> str:
        """
        Get the Contact roll.

        Mirrors Java Contact.getRoll(): base 11-, 1 level -> 8-, levels > 2
        add (levels - 2) to 11.
        """
        roll = 11
        levels = self.levels
        if levels == 1:
            roll = 8
        elif levels > 2:
            roll = 11 + levels - 2
        return f"{roll}-"
