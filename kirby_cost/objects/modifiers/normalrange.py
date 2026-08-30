"""
NormalRange modifier for kirby-cost.

Converted from com.hero.objects.modifiers.NormalRange.java

NormalRange modifier with custom included() method.
Validates Line Of Sight requirement. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class NormalRange(Modifier, xmlid="NORMALRANGE"):
    """
    NormalRange modifier.
    
    Can only be applied to Line Of Sight Powers.
    """
    
    def __init__(self, element=None):
        """Initialize a NormalRange modifier."""
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
        
        if generic_object.range_value != -1:
            return f"{self.display} can only be applied to Line Of Sight Powers."
        
        return ""
