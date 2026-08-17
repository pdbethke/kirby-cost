"""
Lingering modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Lingering.java

Lingering modifier with custom included() method.
Validates duration requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Lingering(Modifier, xmlid="LINGERING"):
    """
    Lingering modifier.
    
    Makes an instant power have a lingering effect.
    """
    
    def __init__(self, element=None):
        """Initialize a Lingering modifier."""
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
        
        if not generic_object.duration == "INSTANT":
            return f"{self._display} can only be placed on Instant abilities."
        
        return ""

    @property
    def limitation(self) -> bool:
        """Lingering is an advantage, not a limitation."""
        return False
