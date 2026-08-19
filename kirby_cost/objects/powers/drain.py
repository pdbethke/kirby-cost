"""
Drain power class for kirby-cost.

Converted from com.hero.objects.powers.Drain.java

Drain reduces characteristics temporarily.
"""

from kirby_cost.objects.powers.power import Power


class Drain(Power, xmlid="DRAIN"):
    """
    Drain power.
    
    Reduces characteristics temporarily (or Suppress in 6E with COSTENDTOMAINTAIN).
    """
    
    def __init__(self):
        """Initialize a Drain power."""
        super().__init__()
        self.xmlid = Drain.XMLID
        self._duration = "INSTANT"
    
    @property
    def alias(self) -> str:
        """Get alias (Drain or Suppress in 6E)."""
        # Stub: would check if 6E and has COSTENDTOMAINTAIN modifier
        # For now, return base alias
        return self._alias or "Drain"
    
    @property
    def damage_display(self) -> str:
        """Get drain display string."""
        return f"{self._levels}d6"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        if self.input and self.input.strip():
            output += f" {self.input}"
        output += f" {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self._selected_option:
            output += f" ({self._selected_option.alias})"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += f", {adder_str}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    @property
    def adder_string(self) -> str:
        """Get adder string (stub)."""
        return ""
    

