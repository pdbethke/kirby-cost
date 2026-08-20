"""
Telepathy power class for kirby-cost.

Converted from com.hero.objects.powers.Telepathy.java

Telepathic communication power.
"""

from kirby_cost.objects.powers.power import Power


class Telepathy(Power, xmlid="TELEPATHY"):
    """
    Telepathy power.
    
    Telepathic communication power.
    """
    
    def __init__(self):
        """Initialize a Telepathy power."""
        super().__init__()
        self.xmlid = Telepathy.XMLID
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
    
    

