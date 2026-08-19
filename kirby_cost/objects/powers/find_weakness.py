"""
Find Weakness power class for kirby-cost.

Converted from com.hero.objects.powers.FindWeakness.java

Ability to find weaknesses in defenses.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class FindWeakness(Power, xmlid="FINDWEAKNESS"):
    """
    Find Weakness power.
    
    Ability to find weaknesses in defenses.
    """
    
    def __init__(self):
        """Initialize a Find Weakness power."""
        super().__init__()
        self.xmlid = FindWeakness.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get find weakness roll display."""
        roll = 11 + int(round_down(float(self._levels) / self._level_value)) if self._level_value != 0.0 else 11 + self._levels
        return f"{roll}-"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        if self._selected_option:
            output += f" with {self._selected_option.alias}"
        
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
    

