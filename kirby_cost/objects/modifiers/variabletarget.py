"""
VariableTarget modifier for kirby-cost.

Converted from com.hero.objects.modifiers.VariableTarget.java

VariableTarget modifier with custom included() method.
Validates duration and attack type requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class VariableTarget(Modifier, xmlid="VARIABLETARGETS"):
    """
    VariableTarget modifier.
    
    Power can target variable number of targets.
    """
    
    def __init__(self, element=None):
        """Initialize a VariableTarget modifier."""
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
        
        if generic_object.duration == "INSTANT":
            return f"{self._display} can only be applied to Constant Attack abilities."
        types = generic_object.types
        if not types or "ATTACK" not in types:
            return f"{self._display} can only be applied to Constant Attack abilities."
        
        return ""
