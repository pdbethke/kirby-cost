"""
Flash power class for kirby-cost.

Converted from com.hero.objects.powers.Flash.java

Flash blinds sense groups.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class Flash(SenseAffectingPower, xmlid="FLASH"):
    """
    Flash power.
    
    Blinds specified sense groups.
    """
    
    def __init__(self):
        """Initialize a Flash power."""
        super().__init__()
        self.xmlid = Flash.XMLID
        self._duration = "INSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get flash display string."""
        return f"{self._levels}d6"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        # Stub: would build sense group list from selected option and adders
        output = f"{self._alias} {self.damage_display}"
        
        if self._selected_option:
            output += f" {self._selected_option.alias}"
        
        # Add additional sense groups from adders (stub)
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
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
    

