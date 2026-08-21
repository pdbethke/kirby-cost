"""
CostsENDToMaintain modifier for kirby-cost.

Converted from com.hero.objects.modifiers.CostsENDToMaintain.java

CostsENDToMaintain modifier with custom included() method.
Validates duration, END cost, and modifier conflicts. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class CostsENDToMaintain(Modifier, xmlid="COSTSENDTOMAINTAIN"):
    """
    CostsENDToMaintain modifier.
    
    Costs END to maintain.
    """
    
    def __init__(self, element=None):
        """Initialize a CostsENDToMaintain modifier."""
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
        
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "REDUCEDEND"):
            return f"{self._display} cannot be applied to an ability with Reduced END."
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "COSTSEND"):
            return f"{self._display} cannot be applied to an ability with Costs END."
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "COSTSENDONLYTOACTIVATE"):
            return f"{self._display} cannot be applied to an ability with Costs END Only To Activate (use Costs END instead)."
        if generic_object.end_usage == 0 and generic_object.xmlid.upper() != "DISPEL":
            return f"{self._display} cannot be applied to an ability which does not cost END."
        if generic_object.duration == "INSTANT" and not generic_object.continuing_effect:
            return f"{self._display} can only be applied to abilities which are Constant in duration."
        if generic_object.duration == "INSTANT" and not generic_object.continuing_effect:
            return f"{self._display} can only be applied to abilities which do not already cost END to maintain."
        
        return ""
