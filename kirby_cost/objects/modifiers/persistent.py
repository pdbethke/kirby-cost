"""
Persistent modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Persistent.java

Persistent modifier with custom included() method.
Validates power type and duration requirements.
Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Persistent(Modifier, xmlid="PERSISTENT"):
    """
    Persistent modifier.
    
    Power is persistent.
    """
    
    def __init__(self, element=None):
        """Initialize a Persistent modifier."""
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
        if generic_object.xmlid == "COMBAT_LEVELS":
            return f"{self._display} cannot be applied to Combat Skill Levels of any form."
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "UOO"):
            return ""
        if generic_object.end_usage > 0:
            if template and template.is_6e():
                if not generic_object.costs_end_to_maintain():
                    return f"{self._display} cannot be applied to Powers which cost END only to Activate."
            else:
                return f"{self._display} cannot be applied to Powers which cost END."
        if template and template.is_6e() and generic_object.duration == "INSTANT" and not generic_object.continuing_effect():
            return f"{self._display} cannot be applied to Instant Powers -- apply Constant first."
        if generic_object.duration in ("PERSISTENT", "INHERENT") or generic_object.duration == "PERSISTENT":
            if generic_object.duration == "PERSISTENT" or generic_object.duration == "PERSISTENT":
                return f"{generic_object.display} is already Persistent."
            if generic_object.duration == "INHERENT" and not GenericObject.find_object_by_id(generic_object.assigned_modifiers, "INHERENT"):
                return f"{generic_object.display} is already Inherent."
        return result
        
        return ""
