"""
Healing power class for kirby-cost.

Converted from com.hero.objects.powers.Healing.java

Healing recovers STUN and BODY damage.
"""

from kirby_cost.objects.powers.power import Power


class Healing(Power, xmlid="HEALING"):
    """
    Healing power.
    
    Recovers STUN and BODY damage.
    """
    
    def __init__(self):
        """Initialize a Healing power."""
        super().__init__()
        self.xmlid = Healing.XMLID
        self._duration = "INSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get healing display string."""
        # Check for REGENEXTRATIME modifier
        has_regen_extra = False
        for mod in self.assigned_modifiers:
            if mod.xmlid == "REGENEXTRATIME":
                has_regen_extra = True
                break
        
        if has_regen_extra:
            return f"{self._levels} BODY"
        
        # Standard healing display
        if self.input and self.input.strip():
            return f"{self.input} {self._levels}d6"
        return f"{self._levels}d6"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        has_regen_extra = False
        for mod in self.assigned_modifiers:
            if mod.xmlid == "REGENEXTRATIME":
                has_regen_extra = True
                break
        
        if has_regen_extra:
            output = f"{self._alias} {self._levels} BODY"
        else:
            output = self._alias
            if self.input and self.input.strip():
                output += f" {self.input}"
            output += f" {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self._selected_option:
            output += f", {self._selected_option.alias}"
        
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

