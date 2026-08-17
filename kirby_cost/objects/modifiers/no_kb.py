"""
No Knockback modifier for kirby-cost.

Converted from com.hero.objects.modifiers.NoKB.java

No Knockback prevents a power from doing knockback.
Uses base class methods for validation and formatting.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class NoKB(Modifier, xmlid="NOKB"):
    """
    No Knockback modifier.
    
    Prevents a power from doing knockback.
    Can only be applied to abilities which do Knockback.
    """
    
    def __init__(self, element=None):
        """Initialize a No Knockback modifier."""
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
        
        if not generic_object.does_knockback():
            return f"{self._display} can only be applied to abilities which do Knockback."
        
        return ""


