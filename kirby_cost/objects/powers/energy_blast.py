"""
Energy Blast power class for kirby-cost.

Converted from com.hero.objects.powers.EnergyBlast.java

Energy Blast is a standard ranged attack power.
"""

from kirby_cost.objects.powers.power import Power


class EnergyBlast(Power, xmlid="ENERGYBLAST"):
    """
    Energy Blast power.
    
    Standard ranged attack power that does STUN and BODY damage.
    """
    
    def __init__(self):
        """Initialize an Energy Blast power."""
        super().__init__()
        self.xmlid = EnergyBlast.XMLID
        self.does_damage = True
        self.does_body = True
        self.does_knockback = True
    
    @property
    def damage_display(self) -> str:
        """
        Get damage display string.
        
        Format: "Xd6" or "Xd6+1" or "Xd6-1" or "X 1/2d6"
        """
        damage_str = f"{self._levels}d6"
        
        # Check for damage adders
        plus_one_pip = False
        plus_one_half_die = False
        minus_one_pip = False
        
        for adder in self.assigned_adders:
            if adder.xmlid == "PLUSONEPIP":
                adder.display_in_string = False
                if self._levels > 0:
                    damage_str = f"{self._levels}d6+1"
                else:
                    damage_str = "1 point"
                plus_one_pip = True
            elif adder.xmlid == "PLUSONEHALFDIE":
                adder.display_in_string = False
                damage_str = f"{self._levels} 1/2d6"
                plus_one_half_die = True
            elif adder.xmlid == "MINUSONEPIP":
                adder.display_in_string = False
                damage_str = f"{self._levels + 1}d6-1"
                minus_one_pip = True
        
        # Add standard effect if enabled
        if self.set_use_standard_effect():
            n = 0
            if plus_one_pip:
                n = 1
            elif plus_one_half_die:
                n = 1
            elif minus_one_pip:
                n = -1
            
            stun = self._levels * 3 + n
            body = self._levels + n if self.does_body else 0
            
            if self.does_body:
                damage_str += f" (standard effect: {stun} STUN, {body} BODY)"
            else:
                damage_str += f" (standard effect: {stun} STUN)"
        
        return damage_str
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string for display.
        
        Format: "Power Name Xd6, [adders]; [modifiers]"
        """
        output = f"{self._alias} {self.damage_display}"
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add input (defense type) if present
        # Stub: would check preferences for WG format
        if self.input and self.input.strip():
            output += f" (vs. {self.input})"
        
        # Add selected option
        if self._selected_option:
            output += f", {self._selected_option.alias}"
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f"; {adder_str}"
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f", {adder_str}"
        
        # Add modifiers
        modifier_str = self.modifier_string
        output += modifier_str
        
        # Add END usage note (stub - would check for END Reserve)
        # if self.get_end_usage() > 0:
        #     # Check for END Reserve
        #     output += " (uses Personal END)"  # or " (uses END Reserve)"
        
        return output
    
    @property
    def adder_string(self) -> str:
        """Get adder string for display (stub)."""
        # Would build string from assigned adders (excluding damage adders)
        adders = []
        for adder in self.assigned_adders:
            if adder.xmlid not in ("PLUSONEPIP", "PLUSONEHALFDIE", "MINUSONEPIP"):
                if adder.display_in_string:
                    adders.append(adder.alias)
        return ", ".join(adders)
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string for display (stub)."""
        # Would build string from assigned modifiers
        return ""

