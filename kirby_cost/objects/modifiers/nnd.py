"""
NND modifier for kirby-cost.

Converted from com.hero.objects.modifiers.NND.java

NND modifier with custom getColumn2Output() and included() methods.
Formats defense description. Validates target and defense requirements.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class NND(Modifier, xmlid="NND"):
    """
    NND modifier.
    
    No Normal Defense attack.
    
    Has custom formatting for defense description. Validates target and defense requirements.
    """
    
    def __init__(self, element=None):
        """Initialize a NND modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for NND modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders (they go in separate string)
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.alias + " (" + self.get_fraction(adder.base_cost) + ")"
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
        
        string2 = string2 + self.get_fraction(d) + ")"
        
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
        
        # Can only be applied to abilities which affect others
        target = generic_object.effective_target()
        if target == "SELFONLY" or target == "N/A":
            return f"{self.display} can only be applied to abilities which affect others."
        
        # Can only be applied to abilities which act against standard Defense types
        defense = generic_object.defense
        if defense == "NONE":
            return (f"{self.display} can only be applied to abilities which act against "
                   f"one of the standard Defense types (Normal, Power, Flash, Mental).")
        
        # Cannot be applied with Penetrating
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "PENETRATING") is not None:
            return f"{self.display} cannot be applied to abilities with the Penetrating Advantage."
        
        return ""
