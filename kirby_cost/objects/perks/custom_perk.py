"""
Custom Perk for kirby-cost.

Converted from com.hero.objects.perks.CustomPerk.java

Custom Perk allows user-defined perks with custom roll values.
"""

from typing import Optional
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.io.xml_utility import XMLUtility


class CustomPerk(Perk, xmlid="CUSTOMPERK"):
    """
    Custom Perk.
    
    Allows user-defined perks with custom roll values.
    """
    
    def __init__(self, element=None):
        """Initialize a Custom Perk."""
        super().__init__(element, self.XMLID)
        # CustomPerk carries an explicit numeric roll from the HDC ``ROLL``
        # attribute.  Perk.roll is a *display string* property (used by
        # column2_output via roll.strip()), so we MUST NOT shadow it with an
        # int — store the numeric roll separately and expose it via
        # roll_value, leaving the inherited string ``roll`` property intact.
        self._custom_roll: int = 0

    @property
    def roll_value(self) -> int:
        """
        Get roll value as integer.

        Returns:
            Roll value (0 if not set)
        """
        return self._custom_roll

    def get_save_xml(self):
        """
        Get XML element for saving.

        Returns:
            XML element with roll attribute
        """
        element = super().get_save_xml()
        element.set("ROLL", str(self._custom_roll))
        return element

    def restore_from_save(self, element) -> None:
        """
        Restore from saved XML element.

        Args:
            element: XML element containing saved data
        """
        super().restore_from_save(element)

        # Parse roll value
        roll_str = XMLUtility.get_value(element, "ROLL")
        if roll_str and roll_str.strip():
            try:
                self._custom_roll = int(roll_str)
            except (ValueError, TypeError):
                self._custom_roll = 0
        else:
            self._custom_roll = 0



