"""
DelayedEffect modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DelayedEffect.java

DelayedEffect modifier with custom getColumn2Output() and getLevelInfo() methods.
Formats multiplier for number active. Uses base class included() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DelayedEffect(Modifier, xmlid="DELAYEDEFFECT"):
    """
    DelayedEffect modifier.
    
    Power effect is delayed.
    
    Has custom formatting for multiplier of number active. Uses base class included() method.
    """
    
    def __init__(self, element=None):
        """Initialize a DelayedEffect modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for DelayedEffect modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.alias + " (" + self.fraction(adder.base_cost) + ")"
            d -= adder.base_cost
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add level info if levels > 0
        if self._levels > 0:
            string2 = string2 + self.level_info + "; "
        
        # Add input
        if self.input and self.input.strip():
            string2 = string2 + self.input + "; "
        
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
    
    @property
    def level_info(self) -> str:
        """
        Get level info string.
        
        Returns multiplier for number active.
        """
        if self._levels <= 0:
            return ""
        
        from kirby_cost.util.rounder import round_half_up
        n = int(round_half_up(pow(self.level_power, self._levels)))
        return "x" + str(n) + " number active"
    
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
        # DelayedEffect modifier doesn't override included() in Java source
        return ""
