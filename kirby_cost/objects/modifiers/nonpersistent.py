"""
Nonpersistent modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Nonpersistent.java

Nonpersistent modifier with custom included() method.
Validates duration requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Nonpersistent(Modifier, xmlid="NONPERSISTENT"):
    """
    Nonpersistent modifier.
    
    Power is not persistent.
    """
    
    def __init__(self, element=None):
        """Initialize a Nonpersistent modifier."""
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
        
        from kirby_cost.core.context import EngineContext
        template = EngineContext.active_template()
        if template and template.is_6e():
            if generic_object.duration in ("PERSISTENT", "INHERENT") and generic_object.end_usage == 0:
                return ""
            if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "COSTSENDTOMAINTAIN"):
                return ""
            if not generic_object.duration == "PERSISTENT":
                return f"{self.display} can only be applied to abilities which are Persistent."
        else:
            if generic_object.duration == "PERSISTENT" and generic_object.end_usage == 0:
                return ""
            if not generic_object.duration == "PERSISTENT":
                return f"{self.display} can only be applied to abilities which are Persistent."

        return ""
