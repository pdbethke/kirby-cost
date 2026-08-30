"""
SubjectToRangeModifier modifier for kirby-cost.

Converted from com.hero.objects.modifiers.SubjectToRangeModifier.java

SubjectToRangeModifier modifier with custom included() method.
Validates range requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class SubjectToRangeModifier(Modifier, xmlid="SUBJECTTORANGEMODIFIER"):
    """
    SubjectToRangeModifier modifier.
    
    Makes a power subject to range modifiers.
    """
    
    def __init__(self, element=None):
        """Initialize a SubjectToRangeModifier modifier."""
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
        
        if generic_object.range_value != -1:
            if not GenericObject.find_object_by_id(generic_object.assigned_modifiers, "NORMALRANGE"):
                return f"{self.display} can only be applied to Line Of Sight Powers."
        
        return ""
