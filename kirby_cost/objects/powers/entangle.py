"""
Entangle power class for kirby-cost.

Converted from com.hero.objects.powers.Entangle.java

Entangle immobilizes targets.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class Entangle(Power, xmlid="ENTANGLE"):
    """
    Entangle power.
    
    Immobilizes targets with DEF and BODY values.
    """
    
    def __init__(self):
        """Initialize an Entangle power."""
        super().__init__()
        self.xmlid = Entangle.XMLID
        self.does_damage = True
        self.does_body = True
    
    @property
    def damage_display(self) -> str:
        """Get entangle display string."""
        # Stub: would check if 6E
        is_6e = True
        
        if is_6e:
            damage_str = f"{self._levels}d6"
            # Calculate DEF and BODY from levels
            def_value = int(round_down(float(self._levels) / self._level_value))
            body_value = int(round_down(float(self._levels) / self._level_value))
            return f"{damage_str}, {def_value} DEF, {body_value} BODY"
        else:
            # 5E format
            return f"{self._levels}d6"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
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

