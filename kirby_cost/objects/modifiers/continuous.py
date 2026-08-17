"""
Continuous modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Continuous.java

Continuous modifier with custom included() method.
Validates power type and template version requirements.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Continuous(Modifier, xmlid="CONTINUOUS"):
    """
    Continuous modifier.
    
    Power is continuous duration.
    """
    
    def __init__(self, element=None):
        """Initialize a Continuous modifier."""
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
        from kirby_cost.core.template import Template
        
        if generic_object.xmlid in ("SUPPRESS", "SUCCOR"):
            return ""
        
        if generic_object.duration == "CONSTANT":
            return f"{generic_object.display} is already Constant in duration."
        
        template = EngineContext.active_template()
        if template and template.is_6e():
            if generic_object.duration == "INHERENT":
                return f"{generic_object.display} is an Inherent ability."
            if generic_object.duration == "PERSISTENT":
                return f"{generic_object.display} is already Persistent in duration."
            return ""
        else:
            if generic_object.duration == "INHERENT":
                return f"{generic_object.display} is an Inherent ability."
            if generic_object.duration == "PERSISTENT":
                return f"{generic_object.display} is a Persistent ability."
            return ""
