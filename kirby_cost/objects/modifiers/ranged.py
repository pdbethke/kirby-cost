"""
Ranged modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Ranged.java

Ranged modifier with custom getColumn2Output() and included() methods.
Validates power type restrictions and checks if already ranged.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Ranged(Modifier, xmlid="RANGED"):
    """
    Ranged modifier.
    
    Makes a power ranged.
    
    Has custom validation for power type restrictions. Cannot be applied to Duplication,
    HTH Attack, Self-Only Powers, or powers that are already ranged.
    """
    
    def __init__(self, element=None):
        """Initialize a Ranged modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Ranged modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        
        # Use selected option alias if present
        if self._selected_option is not None:
            string2 = self._selected_option.alias
        
        d = self.total_value
        
        # Handle adders (they go in separate string)
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
        
        # Count parentheses for proper closing
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
        
        # Cannot be applied to Duplication
        from kirby_cost.objects.powers.duplication import Duplication
        if isinstance(generic_object, Duplication):
            return f"{self._display} cannot be applied to Duplication."
        
        # Cannot be applied to HTH Attack
        from kirby_cost.objects.powers.hand_to_hand_attack import HandToHandAttack
        if isinstance(generic_object, HandToHandAttack):
            return f"{self._display} cannot be applied to HTH Attack."
        
        # Can be applied to Reflection
        from kirby_cost.objects.powers.reflection import Reflection
        if isinstance(generic_object, Reflection):
            return ""
        
        # Can be applied if UOO is present
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "UOO") is not None:
            return ""
        
        # Cannot be applied to Self-Only Powers
        target = generic_object.target
        if target.upper() == "SELFONLY":
            return f"{self._display} cannot be applied to Self-Only Powers."
        
        # Cannot be applied if already Ranged
        if generic_object.range_value != 0:
            return f"{generic_object.display} is already Ranged."
        
        return ""
