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
    
    @property
    def column2_output(self) -> str:
        """``Time Limit (1 Turn; +1/4)`` — TimeLimit.java:47.

        Time Limit builds its own line rather than using Modifier's: the
        option goes in the bracket AHEAD of the fraction, separated by a
        semicolon, with the input and comments between them. The generic
        version has no such shape, and inheriting it dropped the option
        entirely — every Time Limit on Bokor printed "Time Limit (+1/4)",
        which does not say how long.

        Java calls recalcOptions() first; this does not. That method
        recomputes which durations are offered from the power's own duration,
        and the costs it feeds are already exact here (186/186 on Bokor), so
        calling it would be a cost path entered for a display reason.

        The option alias comes from ``option_alias`` rather than a resolved
        option object, for the reason that helper documents: this loader does
        not resolve option objects for modifiers, and OPTION_ALIAS in the
        document is the same string HD wrote FROM the option it had.
        """
        from kirby_cost.objects.base import option_alias
        ret = (self.alias or "").strip()
        opt = (option_alias(self) or "").strip()
        if opt:
            ret += " (" + opt
            if self.input and self.input.strip():
                ret += ", " + self.input.strip()
            if (self.comments or "").strip():
                ret += ", " + self.comments.strip()
            ret += "; " + self.get_fraction(self.total_value) + ")"
        else:
            ret += " (" + self.get_fraction(self.total_value) + ")"
        return ret

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
