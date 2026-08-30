"""
DamageOverTime modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DamageOverTime.java

DamageOverTime modifier with custom included() method.
Validates target and duration requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject, option_alias


class DamageOverTime(Modifier, xmlid="DAMAGEOVERTIME"):
    """
    DamageOverTime modifier.
    
    Damage is applied over time.
    
    Has custom validation for target and duration requirements.
    Uses base class getColumn2Output() method.
    """
    
    def __init__(self, element=None):
        """Initialize a DamageOverTime modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for DamageOverTime modifier.
        """
        string = ""
        string2 = ""
        
        if not self.show_option_only:
            string2 = string2 + self._alias
        
        d = self.total_value
        
        # Add selected option (if not in parens)
        if (not self.show_option_in_parens and 
            self._selected_option is not None and
            self._selected_option.display_in_string and
            self._selected_option.alias.strip()):
            string2 = string2 + " " + self._selected_option.alias
            string2 = string2.strip()
        
        # Add input (if not in parens)
        if (not self.show_input_in_parens and 
            self.input and self.input.strip()):
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
        
        # Add selected option (if in parens)
        if (self.show_option_in_parens and 
            self._selected_option is not None and
            self._selected_option.display_in_string and
            self._selected_option.alias.strip()):
            string2 = string2 + self._selected_option.alias.strip() + "; "
        
        # Add INCREMENTS adder
        for adder in self.assigned_adders:
            if adder.xmlid == "INCREMENTS" and adder.selected_option:
                string2 = string2 + option_alias(adder) + " damage increments, "
        
        # Add TIMEBETWEEN adder
        for adder in self.assigned_adders:
            if adder.xmlid == "TIMEBETWEEN" and adder.selected_option:
                string2 = string2 + "damage occurs every " + option_alias(adder) + ", "
        
        # Add other adders
        for adder in self.assigned_adders:
            if (adder.is_selected and 
                adder.xmlid not in ("INCREMENTS", "TIMEBETWEEN") and
                adder.column2_output.strip()):
                string2 = string2 + adder.column2_output.strip() + ", "
        
        # Add input (if in parens)
        if (self.show_input_in_parens and 
            self.input and self.input.strip()):
            # Java is getInputLabel() with no fallback (DamageOverTime
            # .java:132); "Input" was never a string HD prints.
            string2 = string2 + self.input_label + " " + self.input + "; "
        
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
    def total_value(self) -> float:
        """
        Get total value with custom calculation for INCREMENTS and TIMEBETWEEN.
        
        Returns:
            Total modifier value
        """
        d = self.base_cost
        increments_cost = 0.0
        time_between_cost = 0.0
        
        # Process adders
        for adder in self.assigned_adders:
            if adder.xmlid == "INCREMENTS":
                increments_cost = adder.double_total()
            elif adder.xmlid == "TIMEBETWEEN":
                time_between_cost = adder.double_total()
            else:
                d += adder.double_total()
        
        # Add level costs
        if self._level_value > 0.0:
            d += float(self._levels) / self._level_value * self._level_cost
        
        # Process modifiers (ONEDEFENSE doubles increments, LOCKOUT affects time_between)
        advantage_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.xmlid == "ONEDEFENSE":
                increments_cost *= 2.0
            elif modifier.xmlid == "LOCKOUT":
                if time_between_cost > 0.0:
                    time_between_cost = 0.0
                else:
                    time_between_cost *= 2.0
            elif modifier.total_value > 0.0:
                advantage_sum += modifier.total_value
        
        d = d + increments_cost + time_between_cost
        d = d * (1.0 + advantage_sum)
        
        # Apply limitations (excluding ONEDEFENSE and LOCKOUT)
        limitation_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.xmlid not in ("ONEDEFENSE", "LOCKOUT") and modifier.total_value < 0.0:
                limitation_sum += abs(modifier.total_value)
        
        d = d / (1.0 + limitation_sum)
        
        # Round to quarter
        from kirby_cost.util.rounder import round_half_up
        sign = 1
        if d < 0.0:
            sign = -1
        d = abs(d) * 4.0
        d = round_half_up(d)
        d = (d / 4.0) * sign
        
        # Apply min/max limits
        if d < self._minimum_cost and self.min_set:
            return self._minimum_cost
        if d > self._max_cost and self.max_set:
            return self._max_cost
        
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
        
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        if isinstance(generic_object, NakedModifier):
            return ""
        
        types = generic_object.types
        target = generic_object.target
        
        # Can be applied to Attack Powers that affect others and do damage
        if (types and "ATTACK" in types and 
            target not in ("SELFONLY", "N/A") and
            generic_object.does_damage):
            return ""
        
        # Can be applied to Mental Powers
        if types and "MENTAL" in types:
            return ""
        
        # Can be applied to Adjustment Powers that affect others
        if (types and "ADJUSTMENT" in types and 
            target not in ("SELFONLY", "N/A")):
            return ""
        
        return f"{self.display} can only be applied to Attack Powers and Powers which affect others."
