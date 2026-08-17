"""
Regeneration power class for kirby-cost.

Converted from com.hero.objects.powers.Regeneration.java

Regeneration allows the character to recover BODY damage.
"""

from kirby_cost.objects.powers.power import Power


class Regeneration(Power, xmlid="REGENERATION"):
    """
    Regeneration power.
    
    Allows the character to recover BODY damage over time.
    """
    
    def __init__(self):
        """Initialize a Regeneration power."""
        super().__init__()
        self.xmlid = Regeneration.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get regeneration rate display."""
        if self._selected_option:
            return f"{self._levels} BODY per {self._selected_option.alias}"
        return f"{self._levels} BODY"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ({self.damage_display})"
        output = output.strip()
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
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
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

