"""
Damage Reduction power class for kirby-cost.

Converted from com.hero.objects.powers.DamageReduction.java

Reduces damage taken.
"""

from kirby_cost.objects.powers.power import Power


class DamageReduction(Power, xmlid="DAMAGEREDUCTION"):
    """
    Damage Reduction power.
    
    Reduces damage taken by a percentage.
    """
    
    def __init__(self):
        """Initialize a Damage Reduction power."""
        super().__init__()
        self.xmlid = DamageReduction.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage reduction display."""
        return f"{self._levels}d6"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = ""
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  "
        
        if self.input and self.input.strip():
            # Check if selected option is Mental (stub)
            is_mental = False
            if self._selected_option and "Mental" in self._selected_option.display:
                is_mental = True
            if not is_mental:
                output += f"{self.input} "
        
        if self._selected_option:
            output += self._selected_option.alias
        else:
            output += self._alias
        
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
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

