"""
Cramming skill class for kirby-cost.

Converted from com.hero.objects.skills.Cramming.java
"""

from kirby_cost.objects.skills.skill import Skill


class Cramming(Skill, xmlid="CRAMMING"):
    """Cramming skill."""
    
    def __init__(self, xmlid: str = None):
        """Initialize Cramming."""
        super().__init__(xmlid or Cramming.XMLID)
    
    @property
    def roll(self) -> str:
        """Get roll (empty for cramming)."""
        return ""



