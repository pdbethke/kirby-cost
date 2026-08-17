"""
LimitedRange modifier for kirby-cost.

Converted from com.hero.objects.modifiers.LimitedRange.java

LimitedRange modifier with custom included() method.
Validates range requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class LimitedRange(Modifier, xmlid="LIMITEDRANGE"):
    """
    LimitedRange modifier.
    
    Limits the range of a power.
    """
    
    def __init__(self, element=None):
        """Initialize a LimitedRange modifier."""
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
        
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "RANGED"):
            return f"{self._display} cannot be applied to Powers that have taken the Ranged Advantage.  Use the options on the Ranged Advantage instead."
        if generic_object.range_value == 0:
            return f"{self._display} can only be applied to Ranged Powers."
        if generic_object.range_value < 0:
            return f"{self._display}cannot be applied to Line Of Sight Powers.  You should first take the Normal Range Limitation."
        
        return ""
