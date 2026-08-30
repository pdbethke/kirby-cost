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
        
        # Nonpersistent.java:44-54. Java asks
        # HeroDesigner.getActiveTemplate().is6E(); EngineContext.active_template()
        # is None everywhere, so this took its 5E form under every 6E template.
        # The 6E branch also reads getOrigDuration(), not getDuration(), and its
        # else-arm refuses unconditionally once COSTSENDTOMAINTAIN is absent --
        # the port re-tested the duration there and let a case through.
        from kirby_cost.objects.base import is_6e
        from kirby_cost.core.context import EngineContext
        template = EngineContext.active_template()
        if is_6e():
            if (generic_object.orig_duration in ("PERSISTENT", "INHERENT")
                    and generic_object.end_usage == 0):
                return ""
            if GenericObject.find_object_by_id(
                    generic_object.assigned_modifiers, "COSTSENDTOMAINTAIN") is not None:
                return ""
            return f"{self.display} can only be applied to abilities which are Persistent."
        else:
            if generic_object.duration == "PERSISTENT" and generic_object.end_usage == 0:
                return ""
            if not generic_object.duration == "PERSISTENT":
                return f"{self.display} can only be applied to abilities which are Persistent."

        return ""
