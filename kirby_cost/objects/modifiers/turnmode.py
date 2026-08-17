"""
TurnMode modifier for kirby-cost.

Converted from com.hero.objects.modifiers.TurnMode.java

TurnMode modifier with custom included() method.
Validates movement power requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class TurnMode(Modifier, xmlid="TURNMODE"):
    """
    TurnMode modifier.
    
    Adds turn mode to movement powers.
    """
    
    def __init__(self, element=None):
        """Initialize a TurnMode modifier."""
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
        
        from kirby_cost.objects.powers.flight import Flight
        from kirby_cost.objects.powers.gliding import Gliding
        if isinstance(generic_object, (Flight, Gliding)):
            return f"{generic_object.display} already has a Turn Mode."
        
        return ""
