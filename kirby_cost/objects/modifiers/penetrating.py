"""
Penetrating modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Penetrating.java

Penetrating modifier with custom getColumn2Output() and included() methods.
Formats with levels multiplier. Validates target and defense requirements.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Penetrating(Modifier, xmlid="PENETRATING"):
    """
    Penetrating modifier.
    
    Attack is penetrating.
    
    Has custom formatting with levels multiplier. Cannot be applied to Defense Powers or NND attacks.
    """
    
    def __init__(self, element=None):
        """Initialize a Penetrating modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Penetrating modifier.
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
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + ":  "
            string2 = string2 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add levels multiplier if > 1
        if self._levels > 1:
            string2 = string2 + "x" + str(self._levels) + "; "
        
        # Add selected option
        if self._selected_option is not None:
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
        
        # Can be applied to Strength
        from kirby_cost.objects.characteristics.strength import Strength
        if isinstance(generic_object, Strength):
            return ""
        
        # Cannot be applied to Defense Powers
        types = generic_object.types
        if types and "DEFENSE" in types:
            return f"{self._display} cannot be applied to Defense Powers."
        
        # Can only be applied to abilities which require an Attack Roll
        target = generic_object.target
        if target == "SELFONLY" or target == "N/A":
            return f"{self._display} can only be applied to abilities which require an Attack Roll."
        
        # Cannot be applied to No Normal Defense Attacks
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "NND") is not None:
            return f"{self._display} cannot be applied to No Normal Defense Attacks."
        
        return ""
