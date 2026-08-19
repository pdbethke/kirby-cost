"""
Automaton power class for kirby-cost.

Converted from com.hero.objects.powers.Automaton.java

Special power type for automatons.
"""

from kirby_cost.objects.powers.power import Power


class Automaton(Power, xmlid="AUTOMATON"):
    """
    Automaton power.
    
    Special power type indicating the character is an automaton.
    """
    
    def __init__(self):
        """Initialize an Automaton power."""
        super().__init__()
        self.xmlid = Automaton.XMLID
        self._duration = "INHERENT"
        self.target = "SELFONLY"
        self.range = "SELF"
        self.end = 0
        self._display = "Automaton"
        self._level_cost = 0.0
        self._level_value = 0.0
        self._minimum_cost = 15.0
        self._base_cost = 15.0
        self.base_pded_denominator: int = 3
        self.defense_cost_multiplier: int = 3
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Automaton)."""
        return ""
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._selected_option.alias if self._selected_option else self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
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
    

