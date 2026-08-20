"""
Feedback modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Feedback.java

Feedback modifier with custom getColumn2Output() method.
Handles required adders specially. Always a limitation.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Feedback(Modifier, xmlid="FEEDBACK"):
    """
    Feedback modifier.
    
    Power causes feedback damage.
    
    Has custom formatting for required vs non-required adders. Always a limitation.
    """
    
    def __init__(self, element=None):
        """Initialize a Feedback modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Feedback modifier.
        Handles required adders specially.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders (separate required from non-required)
        for adder in self.assigned_adders:
            if adder.is_required:
                adder.display_in_string = False
                continue
            if string:
                string = string + ", "
            string = string + adder.column2_output + " (" + self.get_fraction(adder.base_cost) + ")"
            d -= adder.base_cost
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        # Count parentheses
        n = 0
        n2 = 0
        while string2.find("(", n) >= 0:
            n2 += 1
            n = string2.find("(", n) + 1
        
        n = 0
        while string2.find(")", n) >= 0:
            n2 -= 1
            n = string2.find(")", n) + 1
        
        string2 = string2 + " (" if n2 <= 0 else string2 + "; "
        
        # Add selected option
        if self._selected_option is not None:
            string2 = string2 + self._selected_option.alias + "; "
        
        # Add required adders
        for adder in self.assigned_adders:
            if not adder.is_required:
                continue
            adder.display_in_string = False
            string2 = string2 + adder.column2_output + "; "
            d += adder.double_total(False)
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        # Apply min/max limits
        if d > self._max_cost and self.max_set:
            d = self._max_cost
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        
        string2 = string2 + self.get_fraction(d) + ")"
        n2 -= 1
        
        # Close remaining parentheses
        while n2 > 0:
            string2 = string2 + ")"
            n2 -= 1
        
        # Append non-required adders string
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
    
    @property
    def limitation_modifier(self) -> bool:
        """Feedback is always a limitation."""
        return True

    @property
    def is_limitation(self) -> bool:
        """Always True.

        Java overrides ``isLimitation`` on this modifier rather than inferring
        it, because the general rule gets it wrong: the value can sit at or
        above zero and it is still a limitation. Charges is the one that shows —
        "8 Continuing Charges lasting 1 Turn each (+0)" is worth nothing and
        still belongs after the semicolon.
        """
        return True
