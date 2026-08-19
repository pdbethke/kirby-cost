"""
Clinging power class for kirby-cost.

Converted from com.hero.objects.powers.Clinging.java

Power to cling to surfaces.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_up


class Clinging(Power, xmlid="CLINGING"):
    """
    Clinging power.
    
    Power to cling to surfaces with enhanced STR.
    """
    
    def __init__(self):
        """Initialize a Clinging power."""
        super().__init__()
        self.xmlid = Clinging.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get clinging display."""
        return ""  # Display is in column2_output
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ("
        
        # Check for UOO modifier with UAA option
        has_uoo_uaa = False
        for mod in self.all_assigned_modifiers:
            if mod.xmlid == "UOO" and mod.selected_option and mod.selected_option.xmlid == "UAA":
                has_uoo_uaa = True
                break
        
        if has_uoo_uaa:
            output += f"{self._levels + 10} STR)"
        elif self._levels == 0:
            output += "normal STR)"
        else:
            # Stub: would get STR characteristic
            # For now, just show levels
            output += f"{round_half_up(float(self._levels))} STR)"
        
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
    

