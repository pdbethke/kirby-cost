"""
DoesNotProvideMentalAwareness modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DoesNotProvideMentalAwareness.java

DoesNotProvideMentalAwareness modifier with custom included() method.
Validates power type requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DoesNotProvideMentalAwareness(Modifier, xmlid="DOESNOTPROVIDEMENTALAWARENESS"):
    """
    DoesNotProvideMentalAwareness modifier.
    
    Prevents a power from providing mental awareness.
    """
    
    def __init__(self, element=None):
        """Initialize a DoesNotProvideMentalAwareness modifier."""
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
        
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "BASEDONCON"):
            return "Mental Powers which are based on CON do not provide Mental Awareness and cannot take this Limitation."
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "BOECV"):
            return "Powers with BOECV do not provide Mental Awareness and cannot take this Limitation."
        
        return ""
