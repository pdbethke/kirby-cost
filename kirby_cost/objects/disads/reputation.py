"""
Reputation Disadvantage.

Converted from com.hero.objects.disads.Reputation.java
"""

from kirby_cost.objects.disads.disadvantage import Disadvantage


class Reputation(Disadvantage):
    """Reputation disadvantage - negative reputation."""
    
    def __init__(self, element=None):
        """Initialize Reputation disadvantage."""
        super().__init__(element)
        self.xmlid = "REPUTATION"
    
    @property
    def column2_output(self) -> str:
        """Get formatted output with special separator handling."""
        # Special handling for separator in parentheses
        # (Simplified - full implementation would match Java exactly)
        return super().column2_output



