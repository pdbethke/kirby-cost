"""
VariableEffect modifier for kirby-cost.

Converted from com.hero.objects.modifiers.VariableEffect.java

VariableEffect modifier with custom getColumn2Output() method.
Uses base class included() method for validation (no custom validation needed).

VariableEffect modifier with custom getColumn2Output() method implemented.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class VariableEffect(Modifier, xmlid="VARIABLEEFFECT"):
    """
    VariableEffect modifier.
    
    Power has variable effect.
    
    Requires custom getColumn2Output() implementation for proper formatting.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a VariableEffect modifier."""
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
        # VariableEffect modifier doesn't override included() in Java source
        return ""
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for VariableEffect modifier.
        Handles complex parentheses balancing and adder formatting.
        """
        string = ""
        string2 = ""
        
        # Start with selected option if present
        if self._selected_option is not None:
            string2 = string2 + self._selected_option.alias
        
        d = self.total_value
        
        # Process adders - format with base cost, subtract from total
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.column2_output + " (" + self.get_fraction(adder.base_cost) + ")"
            d -= adder.base_cost
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        # Count parentheses in string2
        n = 0
        paren_count = 0
        while string2.find("(", n) >= 0:
            paren_count += 1
            n = string2.find("(", n) + 1
        
        n = 0
        while string2.find(")", n) >= 0:
            paren_count -= 1
            n = string2.find(")", n) + 1
        
        # Add opening paren or semicolon based on paren count
        if paren_count <= 0:
            string2 = string2 + " ("
        else:
            string2 = string2 + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        # Add fraction of total value
        string2 = string2 + self.get_fraction(d) + ")"
        
        # Close any extra parentheses
        paren_count -= 1
        while paren_count > 0:
            string2 = string2 + ")"
            paren_count -= 1
        
        # Add adders string at the end
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
