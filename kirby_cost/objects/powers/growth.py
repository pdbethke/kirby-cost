"""
Growth power class for kirby-cost.

Converted from com.hero.objects.powers.Growth.java

Power to increase character size.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_up, round_down
import math


class Growth(Power, xmlid="GROWTH"):
    """
    Growth power.
    
    Increases character size, affecting mass, height, and various characteristics.
    """
    
    def __init__(self):
        """Initialize a Growth power."""
        super().__init__()
        self.xmlid = Growth.XMLID
        self._duration = "CONSTANT"
        # Stub: would initialize mass/height multipliers and characteristic increases
    
    @property
    def damage_display(self) -> str:
        """Get growth display (HTML formatted)."""
        return f"<html>{self.plain_damage_display}</html>"
    
    @property
    def plain_damage_display(self) -> str:
        """Get plain growth display string."""
        # Stub: would calculate mass, height, STR, CON, PRE, PD, ED, BODY, STUN, reach, running, KB, OCV, PER
        # For 6E with selected option, would use predefined size categories
        # For now, return simplified version
        if self._selected_option:
            # Stub: would use size category values
            return f"{self._selected_option.alias} size"
        return f"{self._levels} levels"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ({self.plain_damage_display})"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        # In 5E, show selected option; in 6E, it's in display
        is_6e = True  # Stub: would check
        if self._selected_option and not is_6e:
            output += f" ({self._selected_option.alias}"
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f"; {adder_str}"
            output += ")"
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f" ({adder_str})"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    @property
    def adder_string(self) -> str:
        """Get adder string (stub)."""
        return ""
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

