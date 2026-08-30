"""
AVAD modifier for kirby-cost.

Converted from com.hero.objects.modifiers.AVAD.java

AVAD modifier with custom included() method.
Validates power type and target requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class AVAD(Modifier, xmlid="AVAD"):
    """
    AVAD modifier.
    
    Attack Versus Alternate Defense.
    
    Has custom validation for power type and target requirements.
    Uses base class getColumn2Output() method.
    """
    
    def __init__(self, element=None):
        """Initialize a AVAD modifier."""
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
        # Allow DISPEL and TELEPATHY even if base validation fails
        if (result and result.strip() and 
            generic_object.xmlid not in ("DISPEL", "TELEPATHY")):
            return result
        
        if self.force_allow:
            return result
        
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        if isinstance(generic_object, NakedModifier):
            return ""
        
        types = generic_object.types
        if types and "ATTACK" in types:
            return ""
        
        if generic_object.does_damage:
            return ""
        
        target = generic_object.effective_target()
        if (target not in ("SELFONLY", "N/A") or 
            (types and "MENTAL" in types) or 
            generic_object.xmlid in ("DISPEL", "TELEPATHY")):
            return ""
        
        return f"{self.display} can only be applied to Attack Powers and Powers which affect others."
