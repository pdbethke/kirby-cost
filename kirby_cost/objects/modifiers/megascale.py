"""
Megascale modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Megascale.java

Megascale modifier with custom getColumn2Output(), getDialog(), getSaveXML(),
and getScale() methods. Formats scale information and subtracts adder costs from total.
Uses base class included() method for validation.

TODO: Implement custom methods from Java source:
- getColumn2Output() - formats scale and subtracts adder costs
- getDialog() - returns MegascaleDialog (UI layer)
- getSaveXML() - saves SCALE attribute
- getScale() - returns scale string
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Megascale(Modifier, xmlid="MEGASCALE"):
    """
    Megascale modifier.
    
    Power works at megascale distances.
    
    Has custom formatting for scale display and adder cost handling.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a Megascale modifier."""
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
        # Megascale modifier doesn't override included() in Java source
        return ""
    
    # TODO: Implement custom methods from Java source:
    # - getColumn2Output() - formats scale and subtracts adder costs
    # - getDialog() - returns MegascaleDialog (UI layer)
    # - getSaveXML() - saves SCALE attribute
    # - getScale() - returns scale string
