"""
DelayedEND modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DelayedEND.java

DelayedEND modifier with custom getTotalValue() and included() methods.
Doubles value if parent has Autofire. Only applies to Constant/Continuous abilities.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DelayedEND(Modifier, xmlid="DELAYEDEND"):
    """
    DelayedEND modifier.
    
    END cost is delayed.
    
    Has custom value calculation that doubles if parent has Autofire.
    Only applies to Constant/Continuous abilities that cost END.
    """
    
    def __init__(self, element=None):
        """Initialize a DelayedEND modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def total_value(self) -> float:
        """
        Get total value of this modifier.
        
        Doubles value if parent has Autofire.
        """
        d = super().total_value
        
        if self.parent is not None:
            if GenericObject.find_object_by_id(
                self.parent.assigned_modifiers, "AUTOFIRE") is not None:
                d *= 2.0
        
        return d
    
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
        
        # Clone to check without affecting original
        # For now, use directly
        
        # Can only be applied to abilities which cost END to use
        if generic_object.end_usage <= 0:
            return f"{self._display} can only be applied to abilities which cost END to use."
        
        # Can only be applied to Constant/Continuous abilities
        duration = generic_object.duration
        if not duration.upper() == "CONSTANT":
            return f"{self._display} can only be applied to Constant/Continuous abilities."
        
        return ""
