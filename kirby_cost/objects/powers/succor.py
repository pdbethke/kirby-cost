"""
Succor power class for kirby-cost.

Converted from com.hero.objects.powers.Succor.java

Power to temporarily increase characteristics.
"""

from kirby_cost.objects.powers.power import Power


class Succor(Power, xmlid="SUCCOR"):
    """
    Succor power.
    
    Temporarily increases characteristics.
    """
    
    def __init__(self):
        """Initialize a Succor power."""
        super().__init__()
        self.xmlid = Succor.XMLID
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
        
        if self.input and self.input.strip():
            output += f"  {self.input}"
        output += f" {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Calculate max increase
        n = self._levels * 6
        for adder in self.assigned_adders:
            if adder.xmlid == "PLUSONEHALFDIE":
                n += 3
            elif adder.xmlid == "MINUSONEPIP":
                n += 3
            elif adder.xmlid == "PLUSONEPIP":
                n += 1
        
        n2 = n
        for adder in self.assigned_adders:
            if adder.xmlid == "INCREASEDMAX":
                n += adder.levels
        
        if n != n2:
            output += f", Can Add Maximum Of {n} Points"
        
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
    
    

