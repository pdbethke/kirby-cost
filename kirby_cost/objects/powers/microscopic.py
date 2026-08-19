"""
Microscopic power class for kirby-cost.

Converted from com.hero.objects.powers.Microscopic.java

Microscopic sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder
import math


class Microscopic(SenseAdder, xmlid="MICROSCOPIC"):
    """
    Microscopic power.
    
    Sense adder that provides microscopic vision.
    """
    
    def __init__(self):
        """Initialize a Microscopic power."""
        super().__init__(Microscopic.XMLID)
        self._duration = "CONSTANT"
        # Stub: would auto-select first option if available
    
    @property
    def damage_display(self) -> str:
        """Get microscopic display."""
        multiplier = int(math.pow(self.level_power, self._levels))
        return f" x{multiplier:,}"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ({self.damage_display})"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Build "with" string
        with_str = " with "
        if self._selected_option:
            with_str += self._selected_option.alias
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                with_str += ", " + adder_str
                # Replace last comma with "and"
                if ", " in with_str:
                    last_comma = with_str.rfind(", ")
                    with_str = with_str[:last_comma] + " and" + with_str[last_comma+1:]
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                with_str += adder_str
                # Replace last comma with "and"
                if ", " in with_str:
                    last_comma = with_str.rfind(", ")
                    with_str = with_str[:last_comma] + " and" + with_str[last_comma+1:]
        
        if with_str.strip() != "with":
            output += with_str
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    

