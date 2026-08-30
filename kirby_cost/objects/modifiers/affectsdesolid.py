"""
AffectsDesolid modifier for kirby-cost.

Converted from com.hero.objects.modifiers.AffectsDesolid.java

AffectsDesolid modifier with custom included() method.
Validates target requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class AffectsDesolid(Modifier, xmlid="AFFECTSDESOLID"):
    """
    AffectsDesolid modifier.
    
    Allows a power to affect desolidified targets.
    """
    
    def __init__(self, element=None):
        """Initialize a AffectsDesolid modifier."""
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
        
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        if isinstance(generic_object, NakedModifier):
            return ""
        types_list = generic_object.types
        if ("ATTACK" not in types_list and "DEFENSE" not in types_list and 
                generic_object.effective_target() in ("SELFONLY", "N/A")):
            return f"{self.display} can only be applied to Defense Powers and Powers which affect others."
        
        return ""
