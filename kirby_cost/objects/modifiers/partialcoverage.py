"""
PartialCoverage modifier for kirby-cost.

Converted from com.hero.objects.modifiers.PartialCoverage.java

PartialCoverage modifier with custom getColumn2Output(), getTotalValue(), 
and included() methods. Calculates coverage based on character size and area.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class PartialCoverage(Modifier, xmlid="PARTIALCOVERAGE"):
    """
    PartialCoverage modifier.
    
    Defense only covers part of body.
    
    Has custom cost calculation based on character size and area coverage.
    Only applies to BODY, Clairsentience, and Defense Powers.
    """
    
    def __init__(self, element=None):
        """Initialize a PartialCoverage modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    def _get_area(self, n: int) -> float:
        """
        Calculate area for given size levels.
        
        Args:
            n: Size level
            
        Returns:
            Area value
        """
        # Note: Would need HeroDesigner.getActiveHero().getCharacteristic(15) for Size
        # For now, simplified calculation
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        # For now, assume 6E
        from kirby_cost.util.rounder import round_half_up
        
        # Simplified - would need actual Size characteristic
        # Base values for 6E
        height_base = 8.0
        width_base = 4.0
        
        if n > 0:
            # Would use characteristic.getHeightIncrease() and getWidthIncrease()
            # Simplified calculation
            height = height_base * pow(2.0, n / 2.0)  # Approximate
            width = width_base * pow(2.0, n / 2.0)
        else:
            height = height_base
            width = width_base
        
        # Volume calculation for 6E
        area = height * width * width
        return area
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for PartialCoverage modifier.
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
        
        # Add coverage info
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        string2 = string2 + "covers " + str(self._levels) + " m^3; "
        
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
    
    @property
    def max_level(self) -> int:
        """
        Get maximum level based on character size.
        
        Returns:
            Maximum level value
        """
        from kirby_cost.util.rounder import round_half_up
        
        # Note: Would need HeroDesigner.getActiveHero().getCharacteristic(15) for Size
        # For now, simplified
        # Would get actual size value and calculate area
        size_value = 0  # Would get from hero
        area = self._get_area(size_value)
        return int(round_half_up(area))
    
    def _get_size_levels(self) -> int:
        """
        Get size levels based on coverage levels.
        
        Returns:
            Size level value
        """
        # Note: Would need HeroDesigner.getActiveHero().getCharacteristic(15) for Size
        # For now, simplified
        size_value = 0  # Would get from hero
        area = self._get_area(size_value)
        n2 = 0
        while float(self._levels) < area and n2 < size_value:
            area = self._get_area(size_value - (n2 + 1))
            n2 += 1
        
        if self._get_area(size_value - n2) < float(self._levels):
            n2 -= 1
        
        if n2 < 0:
            n2 = 0
        
        return n2
    
    @property
    def total_value(self) -> float:
        """
        Get total value of this modifier.
        
        Custom calculation for PartialCoverage.
        """
        from kirby_cost.util.rounder import round_half_up
        
        d = self.base_cost
        
        # Add adder costs
        for adder in self.assigned_adders:
            d += adder.double_total()
        
        # Add size level costs
        if self._level_value > 0.0:
            size_levels = self._get_size_levels()
            d += float(size_levels) / self._level_value * self._level_cost
        
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
        
        # Multiply by 4, round, divide by 4
        d *= 4.0
        sign = 1
        if d < 0.0:
            sign = -1
        d = abs(d)
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
        
        # Can only be applied to BODY, Clairsentience, and Defense Powers
        from kirby_cost.objects.characteristics.body import Body
        from kirby_cost.objects.characteristics.def_ import Def
        from kirby_cost.objects.powers.clairsentience import Clairsentience
        
        types = generic_object.types
        if (not isinstance(generic_object, (Body, Def, Clairsentience)) and
            (not types or "DEFENSE" not in types)):
            return f"{self._display} may only be applied to BODY, Clairsentience, and Defense Powers."
        
        return ""
