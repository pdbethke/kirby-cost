"""
Transform power class for kirby-cost.

Converted from com.hero.objects.powers.Transform.java

Power to transform objects.
"""

from kirby_cost.objects.base import option_alias
from kirby_cost.objects.powers.power import Power


class Transform(Power, xmlid="TRANSFORM"):
    """
    Transform power.
    
    Permanently transforms objects into other forms.
    """
    
    def __init__(self):
        """Initialize a Transform power."""
        super().__init__()
        self.xmlid = Transform.XMLID
        self._duration = "INSTANT"
    
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
        output = f"{self._alias} {self.damage_display}"
        
        # Check for HEALEDBY adder
        healed_by = ""
        for adder in self.assigned_adders:
            if adder.xmlid == "HEALEDBY":
                adder.display_in_string = False
                if adder.selected_option:
                    healed_by = option_alias(adder)
                break
        
        if (self.input and self.input.strip()) or healed_by:
            output += " ("
            if self.input and self.input.strip():
                output += self.input
            if self.input and self.input.strip() and healed_by:
                output += ", "
            output += healed_by
            output += ")"
        
        if self._selected_option:
            output = f"{self._selected_option.alias} {output}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += f", {adder_str}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    

