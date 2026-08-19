"""
Damage Negation power class for kirby-cost.

Converted from com.hero.objects.powers.DamageNegation.java

Negates damage before it's applied.
"""

from kirby_cost.objects.powers.power import Power


class DamageNegation(Power, xmlid="DAMAGENEGATION"):
    """
    Damage Negation power.
    
    Negates damage before it's applied.
    """
    
    def __init__(self):
        """Initialize a Damage Negation power."""
        super().__init__()
        self.xmlid = DamageNegation.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage negation display."""
        return ""  # Display is in column2_output
    
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
        
        # Get PHYSICAL, ENERGY, MENTAL adders
        physical_adder = None
        energy_adder = None
        mental_adder = None
        
        for adder in self.assigned_adders:
            if adder.xmlid == "PHYSICAL":
                physical_adder = adder
                adder.display_in_string = False
            elif adder.xmlid == "ENERGY":
                energy_adder = adder
                adder.display_in_string = False
            elif adder.xmlid == "MENTAL":
                mental_adder = adder
                adder.display_in_string = False
        
        # Build negation string
        negation_parts = []
        if physical_adder and physical_adder.levels > 0:
            negation_parts.append(f"-{physical_adder.levels} DCs Physical")
        if energy_adder and energy_adder.levels > 0:
            negation_parts.append(f"-{energy_adder.levels} DCs Energy")
        if mental_adder and mental_adder.levels > 0:
            negation_parts.append(f"-{mental_adder.levels} DCs Mental")
        
        if negation_parts:
            output += f" ({', '.join(negation_parts)})"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += f", {adder_str}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    

