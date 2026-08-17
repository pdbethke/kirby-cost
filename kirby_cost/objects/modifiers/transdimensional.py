"""
Transdimensional modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Transdimensional.java

Transdimensional modifier with custom getColumn2Output() method.
Formats with parentheses handling and adder display.
Uses base class included() method for validation.

TODO: Implement custom getColumn2Output() method from Java source.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Transdimensional(Modifier, xmlid="TRANSDIMENSIONAL"):
    """
    Transdimensional modifier.
    
    Power works across dimensions.
    
    Requires custom getColumn2Output() implementation for proper formatting.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a Transdimensional modifier."""
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
        
        # No additional validation needed - uses base class validation
        # Transdimensional modifier doesn't override included() in Java source
        return ""
    
    # TODO: Implement custom getColumn2Output() method from Java source
    # Formats with parentheses handling and adder display
