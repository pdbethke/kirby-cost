"""
AlwaysOn modifier for kirby-cost.

Converted from com.hero.objects.modifiers.AlwaysOn.java

AlwaysOn modifier with custom included() method.
Validates duration requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class AlwaysOn(Modifier, xmlid="ALWAYSON"):
    """
    AlwaysOn modifier.
    
    Power is always on.
    """
    
    def __init__(self, element=None):
        """Initialize a AlwaysOn modifier."""
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
        
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "FOCUS"):
            return f"{self._display} may not be applied to abilities with the Focus Limitation."
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "STOPSWHENSTUNNED"):
            return f'{self._display} may not be applied to abilities with the "Stops working if Mentalist is Stunned" Limitation.'
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "STOPSWHENKOD"):
            return f'{self._display} may not be applied to abilities with the "Stops working if Mentalist is Stunned" Knocked Out.'
        duration = generic_object.duration
        if duration not in ("PERSISTENT", "INHERENT"):
            return f"{self._display} may only be applied to abilities which are either Persistent or Inherent"
        if generic_object.end_usage > 0:
            return f"{self._display} may not be applied to abilities which use END"
        
        return ""
