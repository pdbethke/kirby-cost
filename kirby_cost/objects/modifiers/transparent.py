"""
Transparent modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Transparent.java

Transparent modifier with custom getColumn2Output(), getAssignedAdders(),
getAvailableAdders(), and included() methods.
Only applies to ForceWall powers.

TODO: Implement custom methods from Java source:
- getColumn2Output() - formats "to [attack types] Attacks"
- getAssignedAdders() - filters adders based on ForceWall configuration
- getAvailableAdders() - filters adders based on ForceWall configuration
- included() - validates only ForceWall powers
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Transparent(Modifier, xmlid="TRANSPARENT"):
    """
    Transparent modifier.
    
    Defense is transparent to certain attacks.
    
    Only applies to ForceWall powers. Has custom adder filtering logic.
    """
    
    def __init__(self, element=None):
        """Initialize a Transparent modifier."""
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
        
        # TODO: Implement validation logic from Java source
        # Should validate: only applies to ForceWall powers
        # if not isinstance(generic_object, ForceWall):
        #     return "Transparent may only be applied to Force Walls."
        return ""
    
    # TODO: Implement custom methods from Java source:
    # - getColumn2Output() - formats "to [attack types] Attacks"
    # - getAssignedAdders() - filters adders based on ForceWall configuration
    # - getAvailableAdders() - filters adders based on ForceWall configuration
