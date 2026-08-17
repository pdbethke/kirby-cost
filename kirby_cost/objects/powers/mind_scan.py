"""
Mind Scan power class for kirby-cost.

Converted from com.hero.objects.powers.MindScan.java

Power to scan minds.
"""

from kirby_cost.objects.powers.power import Power


class MindScan(Power, xmlid="MINDSCAN"):
    """
    Mind Scan power.
    
    Power to scan minds at range.
    """
    
    def __init__(self):
        """Initialize a Mind Scan power."""
        super().__init__()
        self.xmlid = MindScan.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get mind scan display."""
        return f"{self._levels}d6"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Build mind class list
        mind_classes = []
        if self.input and self.input.strip():
            mind_classes.append(self.input.strip())
        
        for adder in self.assigned_adders:
            if adder.xmlid == "MULTIPLECLASSES":
                adder.display_in_string = False
                mind_classes.append(adder.alias)
        
        if mind_classes:
            output += " ("
            for i, mc in enumerate(mind_classes):
                if i > 0 and i < len(mind_classes) - 1:
                    output += ", "
                elif i > 0:
                    output += " and "
                output += mc
            output += " classes of minds)" if len(mind_classes) > 1 else " class of minds)"
        
        if self._selected_option:
            output += f" ({self._selected_option.alias})"
        
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
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

