"""
Does Knockback modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DoesKB.java

Does Knockback allows a power to do knockback.
Uses base class methods for validation and formatting.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DoesKB(Modifier, xmlid="DOESKB"):
    """
    Does Knockback modifier.
    
    Allows a power to do knockback.
    Can only be applied to abilities which are targeted on others.
    """
    
    def __init__(self, element=None):
        """Initialize a Does Knockback modifier."""
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
        
        # Already does knockback
        if generic_object.does_knockback:
            return f"{generic_object.display} already does Knockback."
        
        # Must target others
        target = generic_object.target
        if target not in ("DCV", "ECV", "HEX"):
            return f"{self.display} can only be applied to abilities which are targeted on others."
        
        return ""


