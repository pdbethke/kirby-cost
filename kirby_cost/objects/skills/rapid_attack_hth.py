"""
RapidAttackHTH skill class for kirby-cost.

Converted from com.hero.objects.skills.RapidAttackHTH.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type


class RapidAttackHTH(Skill, xmlid="RAPID_ATTACK_HTH"):
    """Rapid Attack (Hand-to-Hand) skill."""
    
    _roll_based_default = False
    
    def __init__(self, xmlid: str = None):
        """Initialize RapidAttackHTH."""
        super().__init__(xmlid or RapidAttackHTH.XMLID)
    
    @property
    def roll(self) -> str:
        """Get roll (empty for rapid attack)."""
        return ""
    
    



