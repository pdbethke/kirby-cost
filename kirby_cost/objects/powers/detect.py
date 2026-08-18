"""
Detect power class for kirby-cost.

Converted from com.hero.objects.powers.Detect.java

Power to detect things.
"""

from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.powers.sense import Sense


class Detect(Sense, xmlid="DETECT"):
    """
    Detect power.
    
    Power to detect specific things.
    """

    #: Whether the Detect is an ACTIVE sense — Java reads and writes it
    #: (Detect.java:145, :152) and this port did neither, so 17 characters
    #: exported a Detect that had lost the distinction entirely.
    XML_ATTRS = (
        XMLAttr("ACTIVE", "active", "yesno"),
    )

    def __init__(self):
        """Initialize a Detect power."""
        super().__init__(Detect.XMLID)
        self._duration = "CONSTANT"
        self.active: bool = False
    
    @property
    def damage_display(self) -> str:
        """Get detect display."""
        return f"{self._levels}m range"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Get selected option display
        if self._selected_option:
            option_display = self._selected_option.alias
            # Check for EXTRA adders
            extra_adders = []
            for adder in self.assigned_adders:
                if adder.xmlid == "EXTRA":
                    extra_adders.append(adder.alias)
                    adder.display_in_string = False
            
            if extra_adders:
                option_display += ", " + ", ".join(extra_adders)
                # Replace last comma with "and"
                if ", " in option_display:
                    last_comma = option_display.rfind(", ")
                    option_display = (option_display[:last_comma] + 
                                    " and" + 
                                    option_display[last_comma+1:])
            
            output += " " + option_display
        
        output += " " + self.damage_display
        
        # Add group if multiple groups available
        group = self.group
        available_groups = self.available_groups
        if group and len(available_groups) > 1:
            output += f" ({group.alias})"
        elif group is None and len(available_groups) > 1:
            output += " (Unusual Group)"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += ", " + adder_str
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

