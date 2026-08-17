"""
Does Not Bleed power class for kirby-cost.

Converted from com.hero.objects.powers.DoesNotBleed.java

Does not bleed power.
"""

from kirby_cost.objects.powers.power import Power


class DoesNotBleed(Power, xmlid="DOESNOTBLEED"):
    """
    Does Not Bleed power.
    
    Character does not bleed from damage.
    """
    
    def __init__(self):
        """Initialize a Does Not Bleed power."""
        super().__init__()
        self.xmlid = DoesNotBleed.XMLID
        self._duration = "INHERENT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Does Not Bleed)."""
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

