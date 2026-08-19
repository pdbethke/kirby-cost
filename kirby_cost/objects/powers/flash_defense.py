"""
Flash Defense power class for kirby-cost.

Converted from com.hero.objects.powers.FlashDefense.java

Defense against flash attacks.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class FlashDefense(SenseAffectingPower, xmlid="FLASHDEFENSE"):
    """
    Flash Defense power.
    
    Defense against flash attacks (sense-affecting).
    """
    
    def __init__(self):
        """Initialize a Flash Defense power."""
        super().__init__()
        self.xmlid = FlashDefense.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get flash defense display."""
        return f"{self._levels} points"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output with sense groups."""
        # Stub: would build sense group list from selected option and adders
        output = f"{self._alias} {self.damage_display}"
        
        if self._selected_option:
            output += f" {self._selected_option.alias}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
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
    

