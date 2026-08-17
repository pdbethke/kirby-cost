"""
LineOfSight modifier for kirby-cost.

Converted from com.hero.objects.modifiers.LineOfSight.java

LineOfSight modifier with custom included() method.
Validates range requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class LineOfSight(Modifier, xmlid="LOS"):
    """
    LineOfSight modifier.
    
    Makes a power Line of Sight.
    """
    
    def __init__(self, element=None):
        """Initialize a LineOfSight modifier."""
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
        
        if (GenericObject.find_object_by_id(generic_object.assigned_modifiers, "UOO") and 
                GenericObject.find_object_by_id(generic_object.assigned_modifiers, "RANGED")):
            return ""
        if generic_object.range_value == 0:
            return f"{self._display} can only be applied to Ranged Powers."
        if generic_object.range_value < 0:
            return f"{self._display} is already Line Of Sight."
        
        return ""
