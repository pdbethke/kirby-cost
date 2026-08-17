"""
Shrinking power class for kirby-cost.

Converted from com.hero.objects.powers.Shrinking.java

Power to reduce character size.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_up
import math


class Shrinking(Power, xmlid="SHRINKING"):
    """
    Shrinking power.
    
    Reduces character size, affecting mass, height, and various characteristics.
    """
    
    def __init__(self):
        """Initialize a Shrinking power."""
        super().__init__()
        self.xmlid = Shrinking.XMLID
        self._duration = "CONSTANT"
        # Stub: would initialize mass/height multipliers and characteristic increases
    
    @property
    def damage_display(self) -> str:
        """Get shrinking display (HTML formatted)."""
        return f"<html>{self.plain_damage_display}</html>"
    
    @property
    def plain_damage_display(self) -> str:
        """Get plain shrinking display string."""
        # Stub: would calculate mass, height, STR, BODY, STUN, DCV, PER, KB, reach
        # For now, return simplified version
        return f"{self._levels} levels"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ({self.plain_damage_display})"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        if self._selected_option:
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

