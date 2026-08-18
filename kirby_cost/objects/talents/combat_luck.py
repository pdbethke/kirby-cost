"""
Combat Luck Talent for kirby-cost.

Converted from com.hero.objects.talents.CombatLuck.java

Combat Luck provides PD/ED defense.
"""

from typing import Optional
from kirby_cost.objects.talents.talent import Talent
from kirby_cost.io.xml_utility import XMLUtility


class CombatLuck(Talent, xmlid="COMBAT_LUCK"):
    """
    Combat Luck Talent.
    
    Provides PD/ED defense.
    """
    
    def __init__(self, element=None):
        """Initialize a Combat Luck talent."""
        super().__init__(element, self.XMLID)
        self.affects_primary: bool = False
        self.affects_total: bool = False
        self._levels = self._levels
    
    @property
    def affect_primary(self) -> bool:
        """
        Get whether affects primary.
        
        Returns:
            True if affects primary
        """
        return self.affects_primary
    
    @property
    def affect_total(self) -> bool:
        """
        Get whether affects total.
        
        Returns:
            True if affects total
        """
        if self.affects_primary:
            self.affects_total = True
        return self.affects_total
    
    @property
    def ed_increase(self) -> int:
        """
        Get ED increase per level.
        
        Returns:
            ED increase value
        """
        return 3
    
    @property
    def ed_increase_levels(self) -> int:
        """
        Get ED increase levels.
        
        Returns:
            Levels value
        """
        return 1
    
    @property
    def pd_increase(self) -> int:
        """
        Get PD increase per level.
        
        Returns:
            PD increase value
        """
        return 3
    
    @property
    def pd_increase_levels(self) -> int:
        """
        Get PD increase levels.
        
        Returns:
            Levels value
        """
        return 1
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element with attributes
        """
        element = super().get_save_xml()
        element.set("LEVELS", str(self._levels))
        element.set("AFFECTS_PRIMARY", "Yes" if self.affect_primary else "No")
        element.set("AFFECTS_TOTAL", "Yes" if self.affect_total else "No")
        return element
    
    def _init(self, element) -> None:
        """Read this element. Was restore_from_save."""
        super()._init(element)
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        affects_primary_str = XMLUtility.get_value(element, "AFFECTS_PRIMARY")
        if affects_primary_str and affects_primary_str.strip():
            self.affects_primary = affects_primary_str.strip().upper().startswith("Y")
        
        affects_total_str = XMLUtility.get_value(element, "AFFECTS_TOTAL")
        if affects_total_str and affects_total_str.strip():
            self.affects_total = affects_total_str.strip().upper().startswith("Y")
    
    @affect_primary.setter
    def affect_primary(self, affects: bool) -> None:
        """
        Set whether affects primary.
        
        Args:
            affects: True if affects primary
        """
        self.affects_primary = affects
    
    @affect_total.setter
    def affect_total(self, affects: bool) -> None:
        """
        Set whether affects total.
        
        Args:
            affects: True if affects total
        """
        self.affects_total = affects
    
    @property
    def levels(self) -> int:
        """Get the number of levels."""
        return self._levels

    @levels.setter
    def levels(self, levels: int) -> None:
        """
        Set levels and update alias.

        Args:
            levels: Number of levels
        """
        self._levels = levels
        display = self._display
        pd_increase = (self.pd_increase * self._levels /
                      self.pd_increase_levels)
        ed_increase = (self.ed_increase * self._levels /
                      self.ed_increase_levels)
        alias = display + f" ({pd_increase} PD/{ed_increase} ED)"
        self._alias = alias



