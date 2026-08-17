"""
TwoWeaponFightingHTH skill class for kirby-cost.

Converted from com.hero.objects.skills.TwoWeaponFightingHTH.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class TwoWeaponFightingHTH(Skill, xmlid="TWO_WEAPON_FIGHTING_HTH"):
    """Two-Weapon Fighting (Hand-to-Hand) skill."""
    
    _roll_based_default = False
    
    def __init__(self, xmlid: str = None):
        """Initialize TwoWeaponFightingHTH."""
        super().__init__(xmlid or TwoWeaponFightingHTH.XMLID)
    
    @property
    def roll(self) -> str:
        """Get roll (empty for two-weapon fighting)."""
        return ""
    
    



