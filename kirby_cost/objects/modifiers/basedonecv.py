"""
BasedOnECV modifier for kirby-cost.

Converted from com.hero.objects.modifiers.BasedOnECV.java

BasedOnECV modifier with custom included() method.
Validates power type requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class BasedOnECV(Modifier, xmlid="BOECV"):
    """
    BasedOnECV modifier.
    
    Power is based on ECV instead of OCV.
    
    Has custom validation for power type requirements.
    Uses base class getColumn2Output() method.
    """
    
    def __init__(self, element=None):
        """Initialize a BasedOnECV modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for BasedOnECV modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders (they go in separate string)
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.alias + " (" + self.fraction(adder.base_cost) + ")"
            d -= adder.base_cost
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add input
        if self.input and self.input.strip():
            string2 = string2 + self.input + "; "
        
        # Add selected option
        if (self._selected_option is not None and 
            self._selected_option.alias.strip()):
            string2 = string2 + self._selected_option.alias + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.fraction(d) + ")"
        
        # Append adders string
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
    
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
        
        # Cannot be applied to self-only abilities
        target = generic_object.target
        if target == "SELFONLY" or target == "N/A":
            return f"{self._display} cannot be applied to self-only abilities."
        
        # Cannot be applied to abilities which already target ECV
        if target == "ECV":
            return f"{self._display} cannot be applied to abilities which already target ECV."
        
        return ""
