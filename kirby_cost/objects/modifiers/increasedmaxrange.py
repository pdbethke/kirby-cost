"""
IncreasedMaxRange modifier for kirby-cost.

Converted from com.hero.objects.modifiers.IncreasedMaxRange.java

IncreasedMaxRange modifier with custom getColumn2Output(), getMaxRange(),
and included() methods. Calculates maximum range based on power cost.
"""

from typing import Optional
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class IncreasedMaxRange(Modifier, xmlid="INCREASEDMAXRANGE"):
    """
    IncreasedMaxRange modifier.
    
    Increases maximum range.
    
    Has custom range calculation and formatting. Only applies to Ranged Powers.
    """
    
    def __init__(self, element=None):
        """Initialize a IncreasedMaxRange modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for IncreasedMaxRange modifier.
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
        
        # Add max range
        max_range = self.max_range(self.parent)
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        # For now, assume 6E (meters)
        # Java's NumberFormat groups thousands; `locale.format_string` only
        # does so if a locale has been set, and under the default "C" locale
        # it silently does not — so "24,000m" printed as "24000m".
        string2 = string2 + f"{int(max_range):,}" + "m; "
        
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
        """Get level info string (max range)."""
        max_range = self.max_range(self.parent)
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        return str(max_range) + "m"
    
    def max_range(self, generic_object: Optional[GenericObject]) -> int:
        """
        Calculate maximum range.
        
        Args:
            generic_object: Parent object for calculations
            
        Returns:
            Maximum range in meters or inches
        """
        from kirby_cost.util.rounder import round_half_up
        
        if generic_object is None:
            return 0
        
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        # For now, assume 6E
        d = generic_object.total_cost
        
        # Subtract adders that don't include in base
        for adder in generic_object.assigned_adders:
            if not adder.include_in_base() and not adder.custom:
                d -= adder.total_cost
        
        return int(round_half_up(d * 10.0 * pow(self.level_power, self._levels)))
    
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
        
        # Can only be applied to Ranged Powers
        if generic_object.range_value <= 0:
            return f"{self.display} can only be applied to Ranged Powers."
        
        return ""
