"""
Flight power class for kirby-cost.

Converted from com.hero.objects.powers.Flight.java

Flight is a movement power that allows the character to fly.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class Flight(Power, xmlid="FLIGHT"):
    """
    Flight power.
    
    Movement power that allows the character to fly through the air.
    """
    
    def __init__(self):
        """Initialize a Flight power."""
        super().__init__()
        self.xmlid = Flight.XMLID
        self.affects_primary = True  # Affects primary characteristics
        self._duration = "CONSTANT"
    
    def uses_end(self) -> bool:
        """
        Check if Flight uses END.
        
        In 6E, Flight with GLIDING modifier doesn't use END.
        """
        # Stub: would check if 6E and has GLIDING modifier
        # For now, return True (standard behavior)
        return self.uses_end
    
    @property
    def damage_display(self) -> str:
        """
        Get movement display string.
        
        Format: "Xm" (6E) or "X\"" (5E)
        """
        # Calculate movement from levels
        if self._level_value != 0.0:
            movement = round_down(float(self._levels) / self._level_value)
        else:
            movement = self._levels
        
        # Stub: would check if 6E
        is_6e = True  # Default to 6E
        
        if is_6e:
            return f"{int(movement)}m"
        else:
            return f"{int(movement)}\""
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string for display.
        
        Format: "Power Name Xm, [adders]; [modifiers]"
        """
        output = f"{self._alias} {self.damage_display}"
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add input if present
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        # Add selected option
        if self._selected_option:
            output += f", {self._selected_option.alias}"
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f"; {adder_str}"
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f", {adder_str}"
        
        # Add modifiers
        modifier_str = self.modifier_string
        output += modifier_str
        
        # Add END usage note (stub - would check for END Reserve)
        # if self.get_end_usage() > 0:
        #     output += " (uses Personal END)"  # or " (uses END Reserve)"
        
        return output
    
    @property
    def summable(self) -> bool:
        """Check if Flight can be summed with other movement powers."""
        return True
    
    @property
    def adder_string(self) -> str:
        """Get adder string for display (stub)."""
        # Would build string from assigned adders
        return ""
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string for display (stub)."""
        # Would build string from assigned modifiers
        return ""

