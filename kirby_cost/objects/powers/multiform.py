"""
Multiform power class for kirby-cost.

Converted from com.hero.objects.powers.Multiform.java

Power to have multiple forms.
"""

from kirby_cost.objects.powers.power import Power
from typing import Optional


class Multiform(Power, xmlid="MULTIFORM"):
    """
    Multiform power.
    
    Allows the character to have multiple forms.
    """
    
    def __init__(self):
        """Initialize a Multiform power."""
        super().__init__()
        self.xmlid = Multiform.XMLID
        self._duration = "CONSTANT"
        self.file_path: Optional[str] = None
        self.file_association_last_check: Optional[int] = None
    
    @property
    def damage_display(self) -> str:
        """Get multiform display."""
        return f"{self._levels} form{'s' if self._levels != 1 else ''}"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ({self.damage_display})"
        
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
    
    def clear_file_path(self) -> None:
        """Clear associated file path."""
        self.file_path = None
        self.file_association_last_check = None
    
    

