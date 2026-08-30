"""
Explosion modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Explosion.java

Explosion modifier with custom getColumn2Output(), getTotalValue(), and included() methods.
Formats fade rate and validates target/area requirements.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Explosion(Modifier, xmlid="EXPLOSION"):
    """
    Explosion modifier.
    
    Power explodes on impact.
    
    Has custom fade rate formatting and validation for target/area requirements.
    Cannot be applied with AreaEffect or to powers that already affect area.
    """
    
    def __init__(self, element=None):
        """Initialize a Explosion modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Explosion modifier.
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
        
        # Add selected option (if not "Normal (Radius)")
        if (self._selected_option is not None and 
            self._selected_option.alias.strip() and
            self._selected_option.alias != "Normal (Radius)"):
            string2 = string2 + self._selected_option.alias + "; "
        
        # Add fade rate if levels > 0
        if self._levels > 0:
            n = self._levels
            if (self._selected_option is not None and 
                self._selected_option.level_multiplier != 0):
                n *= self._selected_option.level_multiplier
            if n != 1:
                string2 = string2 + "-1 DC/" + str(n) + "\"; "
        
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
    def total_value(self) -> float:
        """
        Get total value of this modifier.
        
        Custom calculation for Explosion modifier.
        """
        from kirby_cost.util.rounder import round_half_up
        
        d = self.base_cost
        
        # Add adder costs
        for adder in self.assigned_adders:
            d += adder.double_total()
        
        # Add level costs
        if self._level_value > 0.0:
            d += float(self._levels - self._minimum_level) * self._level_cost
        
        # Apply advantages
        advantage_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value > 0.0:
                advantage_sum += modifier.total_value
        
        if advantage_sum > 0.0:
            d = d * (1.0 + advantage_sum)
        
        # Apply limitations
        limitation_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += abs(modifier.total_value)
        
        if limitation_sum > 0.0:
            d = d / (1.0 + limitation_sum)
        
        # Round to quarter
        sign = 1
        if d < 0.0:
            sign = -1
        d = abs(d) * 4.0
        d = round_half_up(d)
        d = (d / 4.0) * sign
        
        # Apply min/max limits
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        if d > self._max_cost and self.max_set:
            d = self._max_cost
        
        return d
    
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
        
        # Can be applied to ChangeEnvironment
        from kirby_cost.objects.powers.change_environment import ChangeEnvironment
        if isinstance(generic_object, ChangeEnvironment):
            return ""
        
        # Cannot be applied if already affects area
        target = generic_object.effective_target()
        if target == "HEX":
            return f"{self.display} cannot be applied to Powers which already affect an area."
        
        # Can only be applied to Powers which are targeted on others
        if target not in ("DCV", "ECV"):
            return f"{self.display} can only be applied to Powers which are targeted on others."
        
        # Cannot be applied with AreaEffect
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "AOE") is not None:
            return f"{self.display} cannot be applied to abilities which already affect an area."
        
        return ""
