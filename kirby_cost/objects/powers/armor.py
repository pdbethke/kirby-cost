"""
Armor power class for kirby-cost.

Converted from com.hero.objects.powers.Armor.java

Armor provides resistant defense against physical and energy attacks.
"""

from kirby_cost.objects.powers.power import Power


class Armor(Power, xmlid="ARMOR"):
    """
    Armor power.
    
    Provides resistant defense (PD and ED).
    """
    
    def __init__(self):
        """Initialize an Armor power."""
        super().__init__()
        self.xmlid = Armor.XMLID
        self._duration = "CONSTANT"
        self.resistant_defenses = True
        self._defense = "PD/ED"  # Physical and Energy Defense
        self.can_affect_primary = True
        self.pd_levels: int = 0
        self.ed_levels: int = 0
    
    @property
    def levels(self) -> int:
        """Get total levels (PD + ED)."""
        return self.pd_levels + self.ed_levels

    @levels.setter
    def levels(self, value) -> None:
        self._levels = value
    
    @property
    def damage_display(self) -> str:
        """
        Get defense display string.
        
        Format: "" (empty - PD/ED shown in column output)
        """
        # Armor returns empty string - PD/ED shown in column output
        return ""
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string for display.
        
        Format: "Power Name (X PD/X ED), [adders]; [modifiers]"
        """
        output = f"{self._alias} {self.damage_display}"
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add PD/ED values
        output += f"({self.pd_levels} PD/{self.ed_levels} ED)"
        
        # Add input if present
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        # Add selected option
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
        
        # Add modifiers
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    

