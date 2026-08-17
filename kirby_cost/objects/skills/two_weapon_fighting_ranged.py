"""
TwoWeaponFightingRanged skill class for kirby-cost.

Converted from com.hero.objects.skills.TwoWeaponFightingRanged.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class TwoWeaponFightingRanged(Skill, xmlid="TWO_WEAPON_FIGHTING_RANGED"):
    """Two-Weapon Fighting (Ranged) skill."""
    
    _roll_based_default = False
    
    def __init__(self, xmlid: str = None):
        """Initialize TwoWeaponFightingRanged."""
        super().__init__(xmlid or TwoWeaponFightingRanged.XMLID)
    
    @property
    def roll(self) -> str:
        """Get roll (empty for two-weapon fighting)."""
        return ""
    
    



