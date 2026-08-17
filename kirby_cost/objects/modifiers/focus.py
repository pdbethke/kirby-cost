"""
Focus modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Focus.java

Focus modifier with custom included() method.
Validates power type restrictions. Uses base class getColumn2Output().
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Focus(Modifier, xmlid="FOCUS"):
    """
    Focus modifier.
    
    Power requires a focus.
    
    Has custom validation for power type restrictions.
    Uses base class getColumn2Output() method.
    """
    
    def __init__(self, element=None):
        """Initialize a Focus modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    def included(self, generic_object: GenericObject) -> str:
        """
        Check if this modifier can be applied to the given object.
        
        Args:
            generic_object: The object to check
            
        Returns:
            Empty string if allowed, error message if not
        """
        result = super().included(generic_object)
        if result and result.strip():
            return result
        
        if self.force_allow:
            return result
        
        # Focus can generally be applied to any power
        return ""
    
    @property
    def column2_output(self) -> str:
        """
        Get the column 2 output string for this modifier.
        
        Returns:
            Formatted string for display
        """
        adder_string = ""
        result = ""
        result = result + self._alias
        
        mobility = ""
        breakability = ""
        expendability = ""
        expendability_option = ""
        
        total_value = self.total_value
        
        for adder in self.assigned_adders:
            if adder.xmlid == "MOBILITY" and adder.selected_option:
                mobility = adder.selected_option.alias
                continue
            if adder.xmlid == "BREAKABILITY" and adder.selected_option:
                breakability = adder.selected_option.alias
                continue
            if adder.xmlid == "EXPENDABILITY":
                expendability = "Expendable"
                if adder.selected_option:
                    expendability_option = adder.selected_option.alias
                continue
            if adder_string:
                adder_string = adder_string + ", "
            adder_string = adder_string + adder.alias
        
        if self.input and self.input.strip():
            if result.strip():
                result = result + ":  "
            result = result + self.input
        
        if self._selected_option:
            result = self._selected_option.alias
        
        result = result + " " + mobility
        result = result.strip()
        result = result + " " + breakability
        result = result.strip()
        result = result + " " + expendability
        result = result.strip()
        
        for modifier in self.assigned_modifiers:
            result = result + ", " + modifier.alias
        
        result = result + " ("
        
        if self._alias != self._display:
            result = result + self._alias + "; "
        
        if expendability_option.strip():
            result = result + expendability_option + "; "
        
        if self.comments and self.comments.strip():
            result = result + self.comments + "; "
        
        if adder_string.strip():
            result = result + adder_string + "; "
        
        result = result + self.fraction(total_value) + ")"
        
        return result
    
    @property
    def selected_option(self):
        """Get the selected option."""
        return self._selected_option

    @selected_option.setter
    def selected_option(self, adder):
        """
        Set the selected option for this modifier.
        
        Args:
            adder: The adder to select
        """
        alias = self._alias
        if not alias:
            alias = self._display
        
        old_option_alias = ""
        if self._selected_option:
            old_option_alias = self._selected_option.alias
            if not old_option_alias:
                old_option_alias = self._selected_option.display
        
        self._selected_option = adder
