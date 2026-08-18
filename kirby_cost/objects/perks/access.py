"""
Access Perk for kirby-cost.

Converted from com.hero.objects.perks.Access.java

Access represents access to resources, locations, or information.
"""

from typing import Optional
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.io.xml_utility import XMLUtility


class Access(Perk, xmlid="ACCESS"):
    """
    Access Perk.
    
    Represents access to resources, locations, or information.
    """
    
    def __init__(self, element=None):
        """Initialize an Access perk."""
        super().__init__(element, self.XMLID)
    
    def _init(self, element) -> None:
        """Read this element. Was restore_from_save."""
        super()._init(element)
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        # Save original base cost
        original_base_cost = self._base_cost
        
        # Call parent restore
        
        # If base cost is positive, use it as levels
        if self._base_cost > 0.0:
            self._levels = int(self._base_cost)
        
        # Restore original base cost
        self._base_cost = original_base_cost



