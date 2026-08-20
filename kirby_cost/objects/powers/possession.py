"""
Possession power class for kirby-cost.

Converted from com.hero.objects.powers.Possession.java

Power to possess other beings.
"""

from kirby_cost.objects.powers.power import Power


class Possession(Power, xmlid="POSSESSION"):
    """
    Possession power.
    
    Power to take control of another being's body.
    """
    
    def __init__(self):
        """Initialize a Possession power."""
        super().__init__()
        self.xmlid = Possession.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Power's, unchanged — Java has no getDamageDisplay on this class.

        The override was a bare "{levels}d6", which drops the pip adders and
        the "(standard effect: N points)" note. Ten powers carried the same
        four lines; none of them appears in Java's list of 99
        getDamageDisplay overrides.
        """
        return super().damage_display
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Build required adder string
        required_str = ""
        for adder in self.assigned_adders:
            if adder.is_required:
                if required_str:
                    required_str += "; "
                if adder.xmlid == "MINDCONTROLEFFECT":
                    required_str += f"Mind Control Effect Roll {40 + adder.levels}"
                elif adder.xmlid == "TELEPATHYEFFECT":
                    required_str += f"Telepathy Effect Roll {30 + adder.levels}"
                else:
                    required_str += adder.alias.strip()
                adder.display_in_string = False
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        if required_str or self._selected_option or self.adder_string:
            output += " ("
            if required_str:
                output += required_str
            if self._selected_option:
                if required_str:
                    output += "; "
                output += self._selected_option.alias
                adder_str = self.adder_string
                if adder_str and adder_str.strip():
                    output += f"; {adder_str}"
            elif self.adder_string:
                if required_str:
                    output += "; "
                output += self.adder_string
            output += ")"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    

