"""
LimitedArcOfFire modifier for kirby-cost.

Converted from com.hero.objects.modifiers.LimitedArcOfFire.java

LimitedArcOfFire modifier with custom included() method.
Validates range and target requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class LimitedArcOfFire(Modifier, xmlid="LIMITEDARCOFFIRE"):
    """
    LimitedArcOfFire modifier.
    
    Power has limited arc of fire.
    
    Has custom validation for range and target requirements.
    Uses base class getColumn2Output() method.
    """
    
    def __init__(self, element=None):
        """Initialize a LimitedArcOfFire modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for LimitedArcOfFire modifier.
        """
        string = ""
        string2 = ""
        
        if not self.show_option_only:
            string2 = string2 + self._alias
        
        d = self.total_value
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
        string2 = string2.strip()
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        # Count parentheses
        n = 0
        n2 = 0
        while string2.find("(", n) >= 0:
            n2 += 1
            n = string2.find("(", n) + 1
        
        n = 0
        while string2.find(")", n) >= 0:
            n2 -= 1
            n = string2.find(")", n) + 1
        
        string2 = string2 + " (" if n2 <= 0 else string2 + "; "
        
        # Add selected option
        if (self._selected_option is not None and 
            self._selected_option.display_in_string and
            self._selected_option.alias.strip()):
            string2 = string2 + self._selected_option.alias + "; "
        
        # Add adders
        for adder in self.assigned_adders:
            if not adder.is_selected or not adder.column2_output.strip():
                continue
            string2 = string2 + adder.column2_output.strip() + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        # Apply min/max limits
        if d > self._max_cost and self.max_set:
            d = self._max_cost
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        
        string2 = string2 + self.get_fraction(d) + ")"
        n2 -= 1
        
        # Close remaining parentheses
        while n2 > 0:
            string2 = string2 + ")"
            n2 -= 1
        
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
        
        # Can only be applied to abilities which are targeted on others
        target = generic_object.effective_target()
        if target == "SELFONLY" or target == "N/A":
            return f"{self.display} may only be applied to abilities which are targeted on others."
        
        return ""
