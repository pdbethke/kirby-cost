"""
Inherent modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Inherent.java

Inherent modifier with custom included() method.
Validates duration requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Inherent(Modifier, xmlid="INHERENT"):
    """
    Inherent modifier.
    
    Makes a power inherent.
    """
    
    def __init__(self, element=None):
        """Initialize a Inherent modifier."""
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
        
        if generic_object.end_usage > 0:
            return f"{self._display} cannot be applied to abilities which cost END."
        if not generic_object.duration == "PERSISTENT":
            return f"{self._display} can only be applied to abilities which are Persistent."
        
        return ""
