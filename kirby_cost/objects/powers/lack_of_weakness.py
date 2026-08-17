"""
Lack of Weakness power class for kirby-cost.

Converted from com.hero.objects.powers.LackOfWeakness.java

Lack of weakness power.
"""

from kirby_cost.objects.powers.power import Power


class LackOfWeakness(Power, xmlid="LACKOFWEAKNESS"):
    """
    Lack of Weakness power.
    
    Reduces Find Weakness effectiveness.
    """
    
    def __init__(self):
        """Initialize a Lack of Weakness power."""
        super().__init__()
        self.xmlid = LackOfWeakness.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Lack of Weakness)."""
        return ""
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        output += f"(-{self._levels})"
        
        if self.input and self.input.strip():
            output += f" for {self.input}"
        
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

