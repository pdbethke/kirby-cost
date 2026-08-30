"""
PhysicalManifestation modifier for kirby-cost.

Converted from com.hero.objects.modifiers.PhysicalManifestation.java

PhysicalManifestation modifier with custom included() method.
Validates duration requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class PhysicalManifestation(Modifier, xmlid="PHYSICALMANIFESTATION"):
    """
    PhysicalManifestation modifier.
    
    May only be applied to Constant Powers.
    """
    
    def __init__(self, element=None):
        """Initialize a PhysicalManifestation modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    def included(self, generic_object: GenericObject) -> str:
        """
        Check if this modifier can be applied to the given object.
        
        Args:
            generic_object: The object to check
            
        Returns:
            Empty string if allowed, error message if not
        """
        result = super().included(generic_object)
        if result and result.strip():
            return result
        
        if self.force_allow:
            return result
        
        if not generic_object.duration == "CONSTANT":
            return f"{self.display} may only be applied to Constant Powers."
        return result
        
        return ""
