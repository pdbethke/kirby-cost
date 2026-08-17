"""
Telescopic power class for kirby-cost.

Converted from com.hero.objects.powers.Telescopic.java

Telescopic sense adder.
"""

from kirby_cost.objects.powers.sense_adder import SenseAdder


class Telescopic(SenseAdder, xmlid="TELESCOPIC"):
    """
    Telescopic power.
    
    Sense adder that provides range modifier bonuses.
    """
    
    def __init__(self):
        """Initialize a Telescopic power."""
        super().__init__(Telescopic.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get telescopic display."""
        return f" +{self._levels} versus Range Modifier"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"+{self._levels} versus Range Modifier"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Build "for" string
        for_str = " for "
        if self._selected_option:
            for_str += self._selected_option.alias
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                for_str += ", " + adder_str
                # Replace last comma with "and"
                if ", " in for_str:
                    last_comma = for_str.rfind(", ")
                    for_str = for_str[:last_comma] + " and" + for_str[last_comma+1:]
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                for_str += adder_str
                # Replace last comma with "and"
                if ", " in for_str:
                    last_comma = for_str.rfind(", ")
                    for_str = for_str[:last_comma] + " and" + for_str[last_comma+1:]
        
        if for_str != " for ":
            output += for_str
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
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

