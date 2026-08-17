"""
Hunted Disadvantage.

Converted from com.hero.objects.disads.Hunted.java
"""

from kirby_cost.objects.disads.disadvantage import Disadvantage


class Hunted(Disadvantage):
    """Hunted disadvantage - character is hunted by enemies."""
    
    def __init__(self, element=None):
        """Initialize Hunted disadvantage."""
        super().__init__(element)
        self.xmlid = "HUNTED"
    
    @property
    def column2_output(self) -> str:
        """Get formatted output with special handling for NCI adder."""
        # Special handling for NCI adder display
        # (Simplified - full implementation would match Java exactly)
        return super().column2_output



