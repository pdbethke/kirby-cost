"""
HoleInTheMiddle modifier for kirby-cost.

Converted from com.hero.objects.modifiers.HoleInTheMiddle.java

HoleInTheMiddle modifier with custom getColumn2Output() and included() methods.
Only applies to area-affecting abilities (HEX target). Formats adders with costs.

TODO: Implement custom methods from Java source:
- getColumn2Output() - formats adders with base costs, subtracts from total
- included() - validates only HEX target abilities
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class HoleInTheMiddle(Modifier, xmlid="HOLEINTHEMIDDLE"):
    """
    HoleInTheMiddle modifier.
    
    Area effect has a hole in the middle.
    
    Only applies to area-affecting abilities. Formats adders with costs.
    """
    
    def __init__(self, element=None):
        """Initialize a HoleInTheMiddle modifier."""
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
        
        # HoleInTheMiddle.java:84-89 -- HD's proxy for "affects an area" is
        # the object's own TARGET being HEX.
        if generic_object.target != "HEX":
            return f"{self._display} can only be applied to abilities which affect an area."
        return ""
    
    # TODO: Implement custom getColumn2Output() method from Java source
    # Formats adders with base costs and subtracts from total value
