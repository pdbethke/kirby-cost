"""
VariableAdvantage modifier for kirby-cost.

Converted from com.hero.objects.modifiers.VariableAdvantage.java

VariableAdvantage modifier with custom getColumn2Output() method.
Uses base class included() method for validation (no custom validation needed).

VariableAdvantage modifier with custom getColumn2Output() method implemented.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class VariableAdvantage(Modifier, xmlid="VARIABLEADVANTAGE"):
    """
    VariableAdvantage modifier.
    
    Power can have variable advantages.
    
    Requires custom getColumn2Output() implementation for proper formatting.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a VariableAdvantage modifier."""
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
        # VariableAdvantage modifier doesn't override included() in Java source
        return ""
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for VariableAdvantage modifier.
        Formats advantage costs and adders.
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
        
        # Calculate advantages value
        level_cost = self._level_cost
        level_value = self._level_value
        if level_cost != 0.0 and level_value != 0.0:
            advantages_value = self.base_cost / (level_cost / level_value)
            string2 = string2 + self.get_fraction(advantages_value) + " Advantages; "
        else:
            string2 = string2 + self.get_fraction(self.base_cost) + " Advantages; "
        
        # Add adders string
        if string.strip():
            string2 = string2 + string + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.get_fraction(d) + ")"
        
        return string2
