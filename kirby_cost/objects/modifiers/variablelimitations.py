"""
VariableLimitations modifier for kirby-cost.

Converted from com.hero.objects.modifiers.VariableLimitations.java

VariableLimitations modifier with custom getColumn2Output() and getTotalValue() methods.
Uses base class included() method for validation (no custom validation needed).

VariableLimitations modifier with custom getColumn2Output() and getTotalValue() methods implemented.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_down, round_half_up


class VariableLimitations(Modifier, xmlid="VARIABLELIMITATIONS"):
    """
    VariableLimitations modifier.
    
    Power can have variable limitations.
    
    Requires custom getColumn2Output() and getTotalValue() implementations.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a VariableLimitations modifier."""
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
        
        # No additional validation needed - uses base class validation
        # VariableLimitations modifier doesn't override included() in Java source
        return ""
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for VariableLimitations modifier.
        Formats limitations requirement and adders.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.alias
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + ":  "
            string2 = string2 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Calculate limitations requirement
        level_cost = self._level_cost
        level_value = self._level_value
        if level_cost != 0.0 and level_value != 0.0:
            d2 = float(self._levels) * level_cost + self.base_cost / (level_cost / level_value)
            d2 = round_down(d2 * 4.0) / 4.0
            string2 = string2 + "requires " + self.get_fraction(d2) + " worth of Limitations; "
        else:
            string2 = string2 + "requires " + self.get_fraction(self.base_cost) + " worth of Limitations; "
        
        # Add adders string
        if string.strip():
            string2 = string2 + string + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.get_fraction(d) + ")"
        
        return string2
    
    @property
    def total_value(self) -> float:
        """
        Get total value with complex calculation.
        
        Includes rounding, modifier handling, and min/max limits.
        """
        d = self.base_cost
        
        # Add adder costs
        for adder in self.assigned_adders:
            d += adder.double_total()
        
        # Add level costs
        level_cost = self._level_cost
        if level_cost != 0.0:
            n = 1
            level_value = self._level_value
            if level_value < 0.0 and level_cost < 0.0:
                n = -1
            d2 = float(self._levels) * level_value * level_cost
            d2 = round_down(d2 * 4.0) / 4.0
            d += d2 * n
        
        # Apply positive modifiers
        d3 = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value > 0.0:
                d3 += modifier.total_value
        
        d4 = d * (1.0 + d3)
        
        # Apply negative modifiers
        d5 = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                d5 += abs(modifier.total_value)
        
        d = d4 / (1.0 + d5)
        
        # Round to nearest 1/4
        d *= 4.0
        n = 1
        if d < 0.0:
            n = -1
        d *= n
        d = round_half_up(d)
        d *= n
        d /= 4.0
        
        # Apply min/max limits
        if d < self._minimum_cost and self.min_set:
            return self._minimum_cost
        if d > self._max_cost and self.max_set:
            return self._max_cost
        
        return d
    
    @property
    def limitation(self) -> bool:
        """Check if this is a limitation."""
        return True
