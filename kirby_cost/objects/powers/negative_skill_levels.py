"""
Negative Skill Levels power class for kirby-cost.

Converted from com.hero.objects.powers.NegativeSkillLevels.java

Negative skill levels power.
"""

from kirby_cost.objects.powers.power import Power


class NegativeSkillLevels(Power, xmlid="NEGATIVESKILLLEVELS"):
    """
    Negative Skill Levels power.
    
    Reduces skill rolls.
    """
    
    def __init__(self):
        """Initialize a Negative Skill Levels power."""
        super().__init__()
        self.xmlid = NegativeSkillLevels.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get negative skill levels display."""
        skill_type = self._selected_option.alias if self._selected_option else "??? Skills"
        return f"-{self._levels} with {skill_type}"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        output += f" ({self.damage_display})"
        
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
    

