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
        
        # Java asks HeroDesigner.getActiveTemplate().is6E() (Continuous.java:49).
        # EngineContext.active_template() is None everywhere, so this took its
        # 5E branch under every 6E template and emitted the 5E literal
        # ("is a Persistent ability.") where HD writes "is already Persistent
        # in duration." Same defect, same fix as Invisible and Persistent.
        from kirby_cost.objects.base import is_6e
        
        if generic_object.xmlid in ("SUPPRESS", "SUCCOR"):
            return ""
        
        # Continuous.java:47,51,54,61,64 all read getOrigDuration(), never
        # getDuration(): the rule asks what the power's DURATION field says,
        # not what the duration modifiers have already made of it.
        if generic_object.orig_duration == "CONSTANT":
            return f"{generic_object.display} is already Constant in duration."
        
        if is_6e():
            if generic_object.orig_duration == "INHERENT":
                return f"{generic_object.display} is an Inherent ability."
            if generic_object.orig_duration == "PERSISTENT":
                return f"{generic_object.display} is already Persistent in duration."
            return ""
        else:
            if generic_object.orig_duration == "INHERENT":
                return f"{generic_object.display} is an Inherent ability."
            if generic_object.orig_duration == "PERSISTENT":
                return f"{generic_object.display} is a Persistent ability."
            return ""
