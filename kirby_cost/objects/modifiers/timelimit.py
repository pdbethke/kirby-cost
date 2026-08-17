"""
TimeLimit modifier for kirby-cost.

Converted from com.hero.objects.modifiers.TimeLimit.java

TimeLimit modifier with custom getColumn2Output(), getTotalValue(), included(),
and recalcOptions() methods. Dynamically generates time limit options based on power duration.

TODO: Implement custom methods from Java source:
- getColumn2Output() - formats selected option with value
- getTotalValue() - calls recalcOptions() then super.getTotalValue()
- included() - validates duration and END cost requirements
- recalcOptions() - generates time limit options based on power type and duration
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class TimeLimit(Modifier, xmlid="TIMELIMIT"):
    """
    TimeLimit modifier.
    
    Power has a time limit.
    
    Dynamically generates time limit options based on power duration and type.
    Has complex option recalculation logic.
    """
    
    def __init__(self, element=None):
        """Initialize a TimeLimit modifier."""
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
        
        # TODO: Implement validation logic from Java source
        # Should validate:
        # - Only applies to Persistent, Constant, or Instant powers
        # - For non-Instant powers that use END, must cost 0 END or cost END only to activate
        return ""
    
    # TODO: Implement custom methods from Java source:
    # - getColumn2Output() - formats selected option with value
    # - getTotalValue() - calls recalcOptions() then super.getTotalValue()
    # - included() - validates duration and END cost requirements
    # - recalcOptions() - generates time limit options based on power type and duration
