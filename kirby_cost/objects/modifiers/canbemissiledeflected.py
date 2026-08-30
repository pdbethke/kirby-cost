"""
CanBeMissileDeflected modifier for kirby-cost.

Converted from com.hero.objects.modifiers.CanBeMissileDeflected.java

CanBeMissileDeflected modifier with custom included() method.
Validates range and target requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class CanBeMissileDeflected(Modifier, xmlid="CANBEMISSILEDEFLECTED"):
    """
    CanBeMissileDeflected modifier.
    
    Allows a power to be missile deflected.
    """
    
    def __init__(self, element=None):
        """Initialize a CanBeMissileDeflected modifier."""
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
        
        if (generic_object.does_damage and generic_object.defense == "NORMAL" and 
                generic_object.effective_target() == "DCV"):
            return f"{generic_object.display} can already be Missile Deflected."
        if generic_object.effective_target() not in ("DCV", "HEX", "ECV", "OCV", "OMCV", "DMCV"):
            return f"{self.display} can only be applied to Attack Powers which are targeted on an opponent."
        
        return ""
