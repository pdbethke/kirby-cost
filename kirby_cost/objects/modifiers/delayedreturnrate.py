"""
DelayedReturnRate modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DelayedReturnRate.java

DelayedReturnRate modifier with custom included() method.
Validates power type requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DelayedReturnRate(Modifier, xmlid="DELAYEDRETURNRATE"):
    """
    DelayedReturnRate modifier.
    
    Power returns/fades at a delayed rate.
    
    Has custom validation for power type requirements.
    Uses base class getColumn2Output() method.
    """
    
    def __init__(self, element=None):
        """Initialize a DelayedReturnRate modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for DelayedReturnRate modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders (they go in separate string)
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.column2_output + " (" + self.get_fraction(adder.base_cost) + ")"
            d -= adder.base_cost
        
        # Add selected option in parentheses
        if self._selected_option is not None:
            string2 = string2 + " (" + self._selected_option.alias
        else:
            string2 = string2 + " ("
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
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
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.get_fraction(d) + ")"
        n2 -= 1
        
        # Close remaining parentheses
        while n2 > 0:
            string2 = string2 + ")"
            n2 -= 1
        
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
        
        # Cannot be applied to Healing
        from kirby_cost.objects.powers.healing import Healing
        if isinstance(generic_object, Healing):
            return f"{generic_object.display} has no return/fade rate (its effects are permanent)."
        
        return ""
