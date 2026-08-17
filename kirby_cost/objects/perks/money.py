"""
Money Perk for kirby-cost.

Converted from com.hero.objects.perks.Money.java

Money represents wealth or financial resources.
"""

from typing import Optional
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.objects.adder import Adder


class Money(Perk, xmlid="MONEY"):
    """
    Money Perk.
    
    Represents wealth or financial resources.
    """
    
    def __init__(self, element=None):
        """Initialize a Money perk."""
        super().__init__(element, self.XMLID)
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element
        """
        return super().get_save_xml()
    
    def restore_from_save(self, element) -> None:
        """
        Restore from saved XML element.
        
        Args:
            element: XML element containing saved data
        """
        super().restore_from_save(element)
        
        # Set selected option base cost to match perk base cost
        selected_option = self._selected_option
        if selected_option:
            selected_option.base_cost = self.base_cost
    
    @property
    def base_cost(self) -> float:
        """Get the base cost."""
        return self._base_cost

    @base_cost.setter
    def base_cost(self, cost: float) -> None:
        """
        Set base cost and update selected option if valid.
        
        Args:
            cost: Base cost to set
        """
        super().base_cost = cost
        
        selected_option = self._selected_option
        if selected_option:
            min_cost = selected_option.minimum_cost
            max_cost = selected_option.max_cost
            if min_cost <= cost <= max_cost:
                selected_option.base_cost = cost



