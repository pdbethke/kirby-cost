"""
UsableOnOthers modifier for kirby-cost.

Converted from com.hero.objects.modifiers.UsableOnOthers.java

UsableOnOthers modifier with custom getColumn2Output(), getAlias(), 
and getAssignedAdders() methods. Formats target counts for SIMULTANEOUSLY and UAA options.
Uses base class included() method for validation.

TODO: Implement custom methods from Java source:
- getColumn2Output() - formats target counts and adders
- getAlias() - returns selected option alias or first option alias
- getAssignedAdders() - filters TARGETS adder for modifier intelligence
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class UsableOnOthers(Modifier, xmlid="UOO"):
    """
    UsableOnOthers modifier.
    
    Power can be used on others.
    
    Has custom formatting for SIMULTANEOUSLY and UAA options with target counts.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a UsableOnOthers modifier."""
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
        # UsableOnOthers modifier doesn't override included() in Java source
        return ""
    
    # TODO: Implement custom methods from Java source:
    # - getColumn2Output() - formats target counts and adders
    # - getAlias() - returns selected option alias or first option alias
    # - getAssignedAdders() - filters TARGETS adder for modifier intelligence
