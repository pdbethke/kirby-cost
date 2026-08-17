"""
Enraged Disadvantage.

Converted from com.hero.objects.disads.Enraged.java
"""

from kirby_cost.objects.disads.disadvantage import Disadvantage
from kirby_cost.objects.base import GenericObject


class Enraged(Disadvantage):
    """Enraged disadvantage - character becomes enraged under certain conditions."""
    
    def __init__(self, element=None):
        """Initialize Enraged disadvantage."""
        super().__init__(element)
        self.xmlid = "ENRAGED"
    
    @property
    def column2_output(self) -> str:
        """Get formatted output with special handling for BERSERK adder."""
        output = self._alias
        output = output + ": "
        
        # Special handling: if input exists and BERSERK adder is present
        if self.input and self.input.strip():
            berserk_adder = GenericObject.find_object_by_id(self.assigned_adders, "BERSERK")
            if berserk_adder:
                berserk_adder.display_in_string = False
                output = output + " " + berserk_adder.alias
            output = output + " " + self.input
        
        # Use parent's modifier/adder formatting
        # (Simplified - full implementation would match Java exactly)
        return super().column2_output



