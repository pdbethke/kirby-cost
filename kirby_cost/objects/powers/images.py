"""
Images power class for kirby-cost.

Converted from com.hero.objects.powers.Images.java

Power to create images.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class Images(SenseAffectingPower, xmlid="IMAGES"):
    """
    Images power.
    
    Creates visual/auditory images.
    """
    
    def __init__(self):
        """Initialize an Images power."""
        super().__init__()
        self.xmlid = Images.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get images display."""
        return f"{self._levels}m radius"
    
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
    
    

