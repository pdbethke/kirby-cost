"""
Aid power class for kirby-cost.

Converted from com.hero.objects.powers.Aid.java

Power to aid characteristics.
"""

from kirby_cost.objects.powers.power import Power


class Aid(Power, xmlid="AID"):
    """
    Aid power.
    
    Temporarily increases characteristics (or Boost in 6E with COSTENDTOMAINTAIN).
    """
    
    def __init__(self):
        """Initialize an Aid power."""
        super().__init__()
        self.xmlid = Aid.XMLID
        self._duration = "INSTANT"
    
    @property
    def alias(self) -> str:
        """Get alias (Aid or Boost in 6E)."""
        # Stub: would check if 6E and has COSTENDTOMAINTAIN modifier
        # For now, return base alias
        return self._alias or "Aid"
    
    @property
    def damage_display(self) -> str:
        """Get aid display."""
        return f"{self._levels}d6"
    
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
            output += f", Can Add Maximum Of {n:,} Points"
        
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
        """Get adder string (excluding INCREASEDMAX)."""
        adders = []
        for adder in self.assigned_adders:
            if adder.xmlid not in ("INCREASEDMAX", "PLUSONEPIP", "PLUSONEHALFDIE", "MINUSONEPIP"):
                if adder.display_in_string:
                    adders.append(adder.alias)
        return ", ".join(adders)
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

