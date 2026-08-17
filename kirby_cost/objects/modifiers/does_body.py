"""
Does BODY modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DoesBODY.java

Does BODY allows a power to do BODY damage.
Uses base class methods for validation and formatting.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DoesBODY(Modifier, xmlid="DOESBODY"):
    """
    Does BODY modifier.
    
    Allows a power to do BODY damage.
    Can only be applied to abilities which damage the target.
    """
    
    def __init__(self, element=None):
        """Initialize a Does BODY modifier."""
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
        
        # Cannot be applied to Flash
        if generic_object.xmlid == "FLASH":
            return f"{self._display} cannot be applied to a Flash Attack."
        
        # Already does BODY
        if generic_object.does_body():
            return f"{generic_object.display} already does BODY Damage."
        
        # Must do damage
        if not generic_object.does_damage:
            return f"{self._display} can only be applied to abilities which damage the target."
        
        return ""


