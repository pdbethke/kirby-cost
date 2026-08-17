"""
Custom Talent for kirby-cost.

Converted from com.hero.objects.talents.CustomTalent.java

Custom Talent allows user-defined talents with custom roll values.
"""

from typing import Optional
from kirby_cost.objects.talents.talent import Talent
from kirby_cost.io.xml_utility import XMLUtility


class CustomTalent(Talent, xmlid="CUSTOMTALENT"):
    """
    Custom Talent.
    
    Allows user-defined talents with custom roll values.
    """
    
    def __init__(self, element=None):
        """Initialize a Custom Talent."""
        super().__init__(element, self.XMLID)
        # Talent.roll is a read-only property returning a DISPLAY STRING.
        # Assigning an int to it raised AttributeError in __init__, so this
        # registered class could never construct and every CUSTOMTALENT fell
        # back to _FallbackObject. Keep the numeric roll in its own field and
        # honour the parent's property contract.
        self._roll: int = 0
        self._minimum_level = -999
    
    @property
    def roll_value(self) -> int:
        """Roll value as an integer (0 if not set)."""
        return self._roll

    @property
    def roll(self) -> str:
        """Display roll, overriding Talent.roll (which is always "")."""
        return f"{self._roll}-" if self._roll else ""
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element with roll attribute
        """
        element = super().get_save_xml()
        element.set("LEVELS", str(self._levels))
        element.set("ROLL", str(self._roll))
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
                self._roll = int(roll_str)
            except (ValueError, TypeError):
                self._roll = 0
        else:
            self._roll = 0



