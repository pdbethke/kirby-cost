"""
Instant modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Instant.java

Instant modifier with custom included() method.
Validates duration requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Instant(Modifier, xmlid="INSTANT"):
    """
    Instant modifier.
    
    Makes a power instant duration.
    """
    
    def __init__(self, element=None):
        """Initialize a Instant modifier."""
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
        
        if (GenericObject.find_object_by_id(generic_object.assigned_modifiers, "CONTINUOUS") or 
                GenericObject.find_object_by_id(generic_object.assigned_modifiers, "PERSISTENT") or 
                GenericObject.find_object_by_id(generic_object.assigned_modifiers, "INHERENT")):
            return f"{self.display} cannot be assigned to an ability which have Continuous, Persistent, or Inherent assigned."
        if generic_object.duration == "INSTANT":
            return f"{generic_object.display} is already Instant."
        if not generic_object.duration == "CONSTANT":
            if generic_object.duration == "PERSISTENT":
                return f"{self.display} cannot be applied to a Persistent ability.  The ability must be made non-Persistent first."
            return f"{self.display} can only be applied to Powers which are Constant."
        
        return ""
