"""
DifficultToDispel modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DifficultToDispel.java

DifficultToDispel modifier with custom getColumn2Output(), getLevelInfo(), and included() methods.
Formats multiplier for Active Points. Cannot be applied to Inherent abilities.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DifficultToDispel(Modifier, xmlid="DIFFICULTTODISPEL"):
    """
    DifficultToDispel modifier.
    
    Power is difficult to dispel.
    
    Has custom formatting for Active Points multiplier. Cannot be applied to Inherent abilities.
    """
    
    def __init__(self, element=None):
        """Initialize a DifficultToDispel modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for DifficultToDispel modifier.
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
        string2 = string2 + self.level_info + "; "
        
        # Add selected option
        if self._selected_option is not None:
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
    
    @property
    def level_info(self) -> str:
        """
        Get level info string.
        
        Returns multiplier for Active Points.
        """
        n = int(pow(self.level_power, self._levels))
        return "x" + str(n) + " Active Points"
    
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
        
        # Cannot be applied to Inherent abilities.
        # DifficultToDispel.java:95-97 -- note the TWO spaces after the first
        # sentence; HD's literal is reproduced exactly.
        duration = generic_object.duration
        if duration == "INHERENT":
            return (f"{self.display} cannot be applied to an Inherent ability.  "
                   f"Inherent abilities cannot be Dispelled.")
        
        return ""
