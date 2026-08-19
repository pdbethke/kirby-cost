"""
Power Defense power class for kirby-cost.

Converted from com.hero.objects.powers.PowerDefense.java

Defense against power attacks.
"""

from kirby_cost.objects.powers.power import Power


class PowerDefense(Power, xmlid="POWERDEFENSE"):
    """
    Power Defense power.
    
    Defense against power attacks.
    """
    
    def __init__(self):
        """Initialize a Power Defense power."""
        super().__init__()
        self.xmlid = PowerDefense.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get defense display."""
        return f"{self._levels} points"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ({self.damage_display})"
        
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
    

