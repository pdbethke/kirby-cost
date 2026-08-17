"""
No Hit Locations power class for kirby-cost.

Converted from com.hero.objects.powers.NoHitLocations.java

No hit locations power.
"""

from kirby_cost.objects.powers.power import Power


class NoHitLocations(Power, xmlid="NOHITLOCATIONS"):
    """
    No Hit Locations power.
    
    Character has no hit locations.
    """
    
    def __init__(self):
        """Initialize a No Hit Locations power."""
        super().__init__()
        self.xmlid = NoHitLocations.XMLID
        self._duration = "INHERENT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for No Hit Locations)."""
        return ""
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
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

