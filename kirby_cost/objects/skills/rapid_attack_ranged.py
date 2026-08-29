"""
RapidAttackRanged skill class for kirby-cost.

Converted from com.hero.objects.skills.RapidAttackRanged.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type


class RapidAttackRanged(Skill, xmlid="RAPID_ATTACK_RANGED"):
    """Rapid Attack (Ranged) skill."""
    
    _roll_based_default = False
    
    def __init__(self, xmlid: str = None):
        """Initialize RapidAttackRanged."""
        super().__init__(xmlid or RapidAttackRanged.XMLID)
    
    @property
    def roll(self) -> str:
        """Get roll (empty for rapid attack)."""
        return ""
    
    



