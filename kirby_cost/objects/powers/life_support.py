"""
Life Support power class for kirby-cost.

Converted from com.hero.objects.powers.LifeSupport.java

Life support power.
"""

from kirby_cost.objects.powers.power import Power


class LifeSupport(Power, xmlid="LIFESUPPORT"):
    """
    Life Support power.
    
    Provides protection from environmental hazards.
    """
    
    def __init__(self):
        """Initialize a Life Support power."""
        super().__init__()
        self.xmlid = LifeSupport.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Life Support)."""
        return ""
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        if self._selected_option:
            output += f" ({self._selected_option.alias})"
        
        # Build adder string from selected adders
        adder_parts = []
        for adder in self.assigned_adders:
            if adder.is_selected and adder.display_in_string and adder.column2_output.strip():
                adder_parts.append(adder.column2_output)
        
        if adder_parts:
            output += f" ({'; '.join(adder_parts)})"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    

