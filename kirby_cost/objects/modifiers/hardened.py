"""
Hardened modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Hardened.java

Hardened modifier with custom getColumn2Output() and included() methods.
Formats with levels multiplier. Can be applied to Entangle.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Hardened(Modifier, xmlid="HARDENED"):
    """
    Hardened modifier.
    
    Defense is hardened against AP attacks.
    
    Has custom formatting with levels multiplier. Can be applied to Entangle.
    """
    
    def __init__(self, element=None):
        """Initialize a Hardened modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Hardened modifier.
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
        
        # Add selected option
        if self._selected_option is not None:
            string2 = string2 + self._selected_option.alias + "; "
        
        # Add levels multiplier if > 1
        if self._levels > 1:
            string2 = string2 + "x" + str(self._levels) + "; "
        
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
        
        # Can be applied to Entangle
        from kirby_cost.objects.powers.entangle import Entangle
        if isinstance(generic_object, Entangle):
            return ""
        
        if self.force_allow:
            return result
        
        return result
