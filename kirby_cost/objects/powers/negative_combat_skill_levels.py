"""
Negative Combat Skill Levels power class for kirby-cost.

Converted from com.hero.objects.powers.NegativeCombatSkillLevels.java

Negative combat skill levels power.
"""

from kirby_cost.objects.powers.power import Power


class NegativeCombatSkillLevels(Power, xmlid="NEGATIVECOMBATSKILLLEVELS"):
    """
    Negative Combat Skill Levels power.
    
    Reduces opponent's combat values.
    """
    
    def __init__(self):
        """Initialize a Negative Combat Skill Levels power."""
        super().__init__()
        self.xmlid = NegativeCombatSkillLevels.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get negative combat skill levels display."""
        cv_type = self.input if self.input and self.input.strip() else "OCV"
        return f"-{self._levels} to opponent's {cv_type}"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        output += f" ({self.damage_display})"
        
        if self._selected_option:
            output += f", {self._selected_option.alias}"
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f"; {adder_str}"
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f", {adder_str}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    

