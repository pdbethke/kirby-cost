"""
HalfRangeModifier modifier for kirby-cost.

Converted from com.hero.objects.modifiers.HalfRangeModifier.java

HalfRangeModifier modifier with custom included() method.
Validates range requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class HalfRangeModifier(Modifier, xmlid="HALFRANGEMODIFIER"):
    """
    HalfRangeModifier modifier.
    
    Reduces range by half.
    """
    
    def __init__(self, element=None):
        """Initialize a HalfRangeModifier modifier."""
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
        
        from kirby_cost.objects.frameworks.multipower import Multipower
        from kirby_cost.objects.frameworks.elemental_control import ElementalControl
        if isinstance(generic_object, (Multipower, ElementalControl)):
            return ""
        if generic_object.range_value <= 0:
            return f"{self.display} can only be applied to Ranged Powers."
        
        return ""
