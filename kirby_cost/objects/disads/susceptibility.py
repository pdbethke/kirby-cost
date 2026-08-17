"""
Susceptibility Disadvantage.

Converted from com.hero.objects.disads.Susceptibility.java
"""

from kirby_cost.objects.disads.disadvantage import Disadvantage


class Susceptibility(Disadvantage):
    """Susceptibility disadvantage - vulnerability to specific effects."""
    
    def __init__(self, element=None):
        """Initialize Susceptibility disadvantage."""
        super().__init__(element)
        self.xmlid = "SUSCEPTIBILITY"
    
    @property
    def column2_output(self) -> str:
        """Get formatted output."""
        # Uses parent implementation with slight separator differences
        return super().column2_output



