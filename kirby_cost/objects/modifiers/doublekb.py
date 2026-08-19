"""
DoubleKB modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DoubleKB.java

DoubleKB modifier with custom getColumn2Output() method.
Uses base class included() method for validation.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DoubleKB(Modifier, xmlid="DOUBLEKB"):
    """
    DoubleKB modifier.
    
    Doubles knockback.
    
    Has custom formatting. Uses base class included() method.
    """
    
    def __init__(self, element=None):
        """Initialize a DoubleKB modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for DoubleKB modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.alias + " (" + self.get_fraction(adder.base_cost) + ")"
            d -= adder.base_cost
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + ":  "
            string2 = string2 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.get_fraction(d) + ")"
        
        # Append adders string
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
    
    @property
    def selected_option(self):
        """Get the selected option."""
        return self._selected_option

    @selected_option.setter
    def selected_option(self, adder) -> None:
        """
        Set the selected option.
        
        Updates alias if ONEANDAHALFTIMES is selected.
        """
        self._selected_option = adder
        if adder is not None and adder.xmlid == "ONEANDAHALFTIMES":
            self._alias = "Does x1 1/2 Knockback"
    
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
        
        # Can only be applied to abilities which do Knockback
        if not generic_object.does_knockback():
            return f"{self._display} can only be applied to abilities which do Knockback."
        
        return ""
