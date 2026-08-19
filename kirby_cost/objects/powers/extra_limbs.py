"""
Extra Limbs power class for kirby-cost.

Converted from com.hero.objects.powers.ExtraLimbs.java

Power to have extra limbs.
"""

from kirby_cost.objects.powers.power import Power


class ExtraLimbs(Power, xmlid="EXTRALIMBS"):
    """
    Extra Limbs power.
    
    Provides additional limbs.
    """
    
    def __init__(self):
        """Initialize an Extra Limbs power."""
        super().__init__()
        self.xmlid = ExtraLimbs.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Extra Limbs)."""
        return ""
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output with limb count."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Remove trailing 's' if only 1 limb
        if self._levels == 1 and output.upper().endswith("S"):
            output = output[:-1]
        
        if self._levels > 0:
            output += f" ({self._levels})"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
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
    

