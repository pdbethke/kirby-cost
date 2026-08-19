"""
Damage Resistance power class for kirby-cost.

Converted from com.hero.objects.powers.DamageResistance.java

Resistance to damage types.
"""

from kirby_cost.objects.powers.power import Power


class DamageResistance(Power, xmlid="DAMAGERESISTANCE"):
    """
    Damage Resistance power.
    
    Provides resistance to specific damage types.
    """
    
    def __init__(self):
        """Initialize a Damage Resistance power."""
        super().__init__()
        self.xmlid = DamageResistance.XMLID
        self._duration = "CONSTANT"
        self.pd_levels: int = 0
        self.ed_levels: int = 0
        self.md_levels: int = 0
        self.fd_levels: int = 0
        self.powd_levels: int = 0
    
    @property
    def damage_display(self) -> str:
        """Get damage resistance display."""
        return ""  # Display is in column2_output
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Build resistance string
        output += "("
        first = True
        if self.pd_levels > 0:
            output += f"{self.pd_levels} PD"
            first = False
        if self.ed_levels > 0:
            if not first:
                output += "/"
            output += f"{self.ed_levels} ED"
            first = False
        if self.md_levels > 0:
            if not first:
                output += "/"
            output += f"{self.md_levels} Mental Def."
            first = False
        if self.fd_levels > 0:
            if not first:
                output += "/"
            output += f"{self.fd_levels} Flash Def."
            first = False
        if self.powd_levels > 0:
            if not first:
                output += "/"
            output += f"{self.powd_levels} Power Def."
        output += ")"
        
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
    

