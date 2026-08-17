"""
Others Only modifier for kirby-cost.

Converted from com.hero.objects.modifiers.OthersOnly.java

Others Only limits a power to only affect others, not self.
Uses base class methods for validation and formatting.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class OthersOnly(Modifier, xmlid="OTHERSONLY"):
    """
    Others Only modifier.
    
    Limits a power to only affect others, not self.
    Can only be applied to Powers which are capable of affecting others.
    """
    
    def __init__(self, element=None):
        """Initialize an Others Only modifier."""
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
        
        target = generic_object.target
        if target in ("SELFONLY", "N/A"):
            return f"{self._display} can only be applied to Powers which are capable of affecting others."
        
        return ""


