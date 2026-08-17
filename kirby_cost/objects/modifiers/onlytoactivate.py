"""
OnlyToActivate modifier for kirby-cost.

Converted from com.hero.objects.modifiers.OnlyToActivate.java

OnlyToActivate modifier with custom included() method.
Validates duration and END cost requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class OnlyToActivate(Modifier, xmlid="ONLYTOACTIVATE"):
    """
    OnlyToActivate modifier.
    
    Limits END cost to activation only.
    """
    
    def __init__(self, element=None):
        """Initialize a OnlyToActivate modifier."""
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
        
        if self.progenitor is not None:
            duration = generic_object.duration
            if duration not in ("CONSTANT", "INHERENT", "PERSISTENT"):
                return f"{self._display} can only be applied to Constant, Persistent, or Inherent abilitiesF."
        
        return ""
