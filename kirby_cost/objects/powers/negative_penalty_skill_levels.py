"""
Negative Penalty Skill Levels power class for kirby-cost.

Converted from com.hero.objects.powers.NegativePenaltySkillLevels.java

Negative penalty skill levels power.
"""

from kirby_cost.objects.powers.power import Power


class NegativePenaltySkillLevels(Power, xmlid="NEGATIVEPENALTYSKILLLEVELS"):
    """
    Negative Penalty Skill Levels power.
    
    Increases hit location modifiers character suffers.
    """
    
    def __init__(self):
        """Initialize a Negative Penalty Skill Levels power."""
        super().__init__()
        self.xmlid = NegativePenaltySkillLevels.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get negative penalty skill levels display."""
        modifier_type = self.input if self.input and self.input.strip() else "Hit Location modifiers"
        attack_type = self._selected_option.alias if self._selected_option else "???"
        return f"increase {modifier_type} character suffers with {attack_type} by -{self._levels}"
    
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
    

