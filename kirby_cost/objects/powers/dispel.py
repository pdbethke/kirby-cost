"""
Dispel power class for kirby-cost.

Converted from com.hero.objects.powers.Dispel.java

Power to dispel other powers.
"""

from kirby_cost.objects.powers.power import Power


class Dispel(Power, xmlid="DISPEL"):
    """
    Dispel power.
    
    Temporarily negates other powers (or Suppress in 6E with COSTENDTOMAINTAIN).
    """
    
    def __init__(self):
        """Initialize a Dispel power."""
        super().__init__()
        self.xmlid = Dispel.XMLID
        self._duration = "INSTANT"
    
    @property
    def duration(self) -> str:
        """Get duration (CONSTANT if COSTENDTOMAINTAIN)."""
        duration = self._duration
        # Stub: would check for COSTENDTOMAINTAIN modifier
        # if self.find_modifier_by_id("COSTENDTOMAINTAIN"):
        #     return "CONSTANT"
        return duration
    
    @property
    def damage_display(self) -> str:
        """Power's, unchanged — Java has no getDamageDisplay on this class.

        The override was a bare "{levels}d6", which drops the pip adders and
        the "(standard effect: N points)" note. Ten powers carried the same
        four lines; none of them appears in Java's list of 99
        getDamageDisplay overrides.
        """
        return super().damage_display
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        # Check for COSTENDTOMAINTAIN (becomes Suppress)
        # Stub: would check modifier
        # if self.find_modifier_by_id("COSTENDTOMAINTAIN"):
        #     output = "Suppress"
        
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
    
    

