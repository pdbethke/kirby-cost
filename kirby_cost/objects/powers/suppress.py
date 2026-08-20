"""
Suppress power class for kirby-cost.

Converted from com.hero.objects.powers.Suppress.java

Power to suppress other powers.
"""

from kirby_cost.objects.powers.power import Power


class Suppress(Power, xmlid="SUPPRESS"):
    """
    Suppress power.
    
    Temporarily reduces other powers.
    """
    
    def __init__(self):
        """Initialize a Suppress power."""
        super().__init__()
        self.xmlid = Suppress.XMLID
        self._duration = "CONSTANT"
    
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
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f" {self.input}"
        output += f" {self.damage_display}"
        output = output.strip()
        
        # Check for VARIABLEEFFECT modifier
        for mod in self.assigned_modifiers:
            if mod.xmlid == "VARIABLEEFFECT":
                output += f", {mod.selected_option.alias} ({self._fraction(mod.total_value)})"
                mod.display_in_string = False
                break
        
        if self._selected_option:
            output += f" ({self._selected_option.alias})"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += f", {adder_str}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    def _fraction(self, value: float) -> str:
        """Convert value to fraction string (stub)."""
        return str(value)
    
    

