"""
Transfer power class for kirby-cost.

Converted from com.hero.objects.powers.Transfer.java

Power to transfer characteristics.
"""

from kirby_cost.objects.powers.power import Power


class Transfer(Power, xmlid="TRANSFER"):
    """
    Transfer power.
    
    Transfers characteristics from one target to another.
    """
    
    def __init__(self):
        """Initialize a Transfer power."""
        super().__init__()
        self.xmlid = Transfer.XMLID
        self._duration = "INSTANT"
    
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
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f" ({self.input})"
        
        # Calculate max transfer
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
            output += f", Can Transfer Maximum Of {n} Points"
        
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
    
    

